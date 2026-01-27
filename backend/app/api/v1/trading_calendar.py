"""
交易日历API路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Body, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Optional, List
import math
import os
import uuid
from pathlib import Path
from datetime import datetime, date, timedelta

from app.database.session import get_db
from app.services.trading_calendar_service import TradingCalendarService
from app.schemas.trading_calendar import (
    TradingCalendarCreate,
    TradingCalendarUpdate,
    TradingCalendarResponse,
    TradingCalendarListResponse,
)
from app.utils.date_utils import parse_date
from app.config import settings

router = APIRouter()

# 图片上传目录
UPLOAD_DIR = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'trading_calendar'))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的图片类型
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


@router.get("/", response_model=TradingCalendarListResponse)
def get_trading_calendar_list(
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    stock_name: Optional[str] = Query(None, description="股票名称（模糊查询）"),
    direction: Optional[str] = Query(None, description="操作方向：买入/卖出"),
    strategy: Optional[str] = Query(None, description="策略：低吸/排板/加仓"),
    source: Optional[str] = Query(None, description="来源"),
    concept_ids: Optional[str] = Query(None, description="概念板块ID列表（逗号分隔，如：1,2,3）"),
    concept_names: Optional[str] = Query(None, description="概念板块名称列表（逗号分隔，如：人工智能,新能源）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    order: str = Query("desc", description="排序方向 asc/desc"),
    db: Session = Depends(get_db)
):
    """获取交易日历列表"""
    # 如果没有提供日期范围，默认使用最近1个月
    if not start_date and not end_date:
        end_date_obj = date.today()
        start_date_obj = end_date_obj - timedelta(days=30)
    else:
        start_date_obj = parse_date(start_date) if start_date else None
        end_date_obj = parse_date(end_date) if end_date else None
    
    # 解析概念板块参数
    concept_ids_list = None
    if concept_ids:
        try:
            concept_ids_list = [int(x.strip()) for x in concept_ids.split(',') if x.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="概念板块ID格式错误")
    
    concept_names_list = None
    if concept_names:
        concept_names_list = [x.strip() for x in concept_names.split(',') if x.strip()]
    
    items, total = TradingCalendarService.get_list(
        db=db,
        start_date=start_date_obj,
        end_date=end_date_obj,
        stock_name=stock_name,
        direction=direction,
        strategy=strategy,
        source=source,
        concept_ids=concept_ids_list,
        concept_names=concept_names_list,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order if order in ("asc", "desc") else "desc",
    )
    
    # 为每个记录加载概念板块
    from app.services.stock_concept_service import StockConceptService
    for item in items:
        concepts = TradingCalendarService.get_concepts_for_calendar(db, item)
        # 将概念板块添加到响应对象（通过动态属性）
        item._concepts = concepts
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return TradingCalendarListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{calendar_id}", response_model=TradingCalendarResponse)
def get_trading_calendar(
    calendar_id: int,
    db: Session = Depends(get_db)
):
    """获取交易日历详情"""
    calendar = TradingCalendarService.get_by_id(db, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="交易日历不存在")
    return calendar


@router.post("/", response_model=TradingCalendarResponse, status_code=201)
def create_trading_calendar(
    calendar_data: TradingCalendarCreate,
    db: Session = Depends(get_db)
):
    """创建交易日历"""
    try:
        calendar = TradingCalendarService.create(db, calendar_data.model_dump())
        return calendar
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")


@router.put("/{calendar_id}", response_model=TradingCalendarResponse)
def update_trading_calendar(
    calendar_id: int,
    calendar_data: TradingCalendarUpdate,
    db: Session = Depends(get_db)
):
    """更新交易日历"""
    import traceback
    import sys
    
    try:
        print(f"[TradingCalendar API] PUT /{calendar_id} - 收到更新请求")
        # 安全地打印请求数据（避免序列化 date 对象）
        request_data_str = {k: str(v) if hasattr(v, 'isoformat') else v for k, v in calendar_data.model_dump().items()}
        print(f"[TradingCalendar API] 请求数据: {request_data_str}")
        sys.stdout.flush()
        
        # 过滤掉 None 值
        update_dict = {k: v for k, v in calendar_data.model_dump().items() if v is not None}
        
        # 安全地打印更新数据
        update_dict_str = {k: str(v) if hasattr(v, 'isoformat') else v for k, v in update_dict.items()}
        print(f"[TradingCalendar API] 过滤后的更新数据: {update_dict_str}")
        sys.stdout.flush()
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        calendar = TradingCalendarService.update(db, calendar_id, update_dict)
        if not calendar:
            raise HTTPException(status_code=404, detail="交易日历不存在")
        
        # 转换为Pydantic模型以确保序列化正确
        response = TradingCalendarResponse.model_validate(calendar)
        print(f"[TradingCalendar API] 更新成功: {calendar_id}")
        sys.stdout.flush()
        # 直接返回 Pydantic 模型，FastAPI 会自动处理序列化
        return response
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        print(f"[TradingCalendar API] 更新失败: {str(e)}")
        traceback.print_exc()
        sys.stdout.flush()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/{calendar_id}", status_code=204)
def delete_trading_calendar(
    calendar_id: int,
    db: Session = Depends(get_db)
):
    """删除交易日历"""
    success = TradingCalendarService.delete(db, calendar_id)
    if not success:
        raise HTTPException(status_code=404, detail="交易日历不存在")
    return None


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传图片"""
    # 检查文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}，仅支持: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # 读取文件内容
    contents = await file.read()
    
    # 检查文件大小
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制: {len(contents) / 1024 / 1024:.2f}MB，最大允许: {MAX_IMAGE_SIZE / 1024 / 1024}MB"
        )
    
    # 生成唯一文件名
    file_ext = Path(file.filename).suffix or '.jpg'
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # 保存文件
    try:
        with open(file_path, 'wb') as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败: {str(e)}")
    
    # 返回文件URL
    file_url = f"/api/v1/trading-calendar/images/{unique_filename}"
    return {"url": file_url, "filename": unique_filename}


@router.get("/images/{filename}")
async def get_image(filename: str):
    """获取图片"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 检查文件是否在允许的目录内（安全措施）
    try:
        file_path.resolve().relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="禁止访问")
    
    return FileResponse(file_path)


# 交易日历概念板块关联API
@router.post("/{calendar_id}/concepts")
def add_concepts_to_calendar(
    calendar_id: int,
    concept_ids: List[int] = Body(..., description="概念板块ID列表"),
    db: Session = Depends(get_db)
):
    """为交易日历添加概念板块（替换所有现有关联）"""
    from app.services.stock_concept_service import TradingCalendarConceptService
    
    concepts = TradingCalendarConceptService.set_concepts_for_calendar(
        db=db,
        calendar_id=calendar_id,
        concept_ids=concept_ids
    )
    
    if not concepts and concept_ids:
        # 检查交易日历是否存在
        calendar = TradingCalendarService.get_by_id(db, calendar_id)
        if not calendar:
            raise HTTPException(status_code=404, detail="交易日历不存在")
    
    return {
        "trading_calendar_id": calendar_id,
        "concepts": [
            {"id": c.id, "name": c.name, "code": c.code}
            for c in concepts
        ]
    }


@router.put("/{calendar_id}/concepts")
def update_calendar_concepts(
    calendar_id: int,
    concept_ids: List[int] = Body(..., description="概念板块ID列表（替换所有关联）"),
    db: Session = Depends(get_db)
):
    """更新交易日历的概念板块（替换所有现有关联）"""
    from app.services.stock_concept_service import TradingCalendarConceptService
    
    concepts = TradingCalendarConceptService.set_concepts_for_calendar(
        db=db,
        calendar_id=calendar_id,
        concept_ids=concept_ids
    )
    
    # 检查交易日历是否存在
    calendar = TradingCalendarService.get_by_id(db, calendar_id)
    if not calendar:
        raise HTTPException(status_code=404, detail="交易日历不存在")
    
    return {
        "trading_calendar_id": calendar_id,
        "concepts": [
            {"id": c.id, "name": c.name, "code": c.code}
            for c in concepts
        ]
    }


@router.delete("/{calendar_id}/concepts/{concept_id}", status_code=204)
def remove_concept_from_calendar(
    calendar_id: int,
    concept_id: int,
    db: Session = Depends(get_db)
):
    """删除交易日历的概念板块关联"""
    from app.services.stock_concept_service import TradingCalendarConceptService
    
    success = TradingCalendarConceptService.remove_concept_from_calendar(
        db=db,
        calendar_id=calendar_id,
        concept_id=concept_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="关联关系不存在")
    return None

