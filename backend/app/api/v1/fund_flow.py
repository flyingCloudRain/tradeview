"""
资金流API路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import math

from app.database.session import get_db
from app.services.fund_flow_service import FundFlowService
from app.utils.date_utils import parse_date, get_trading_date
from app.config import settings

router = APIRouter()


@router.get("/")
def get_fund_flow_list(
    date: str = Query(..., description="日期"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    concept_ids: Optional[str] = Query(None, description="概念板块ID列表（逗号分隔，如：1,2,3）"),
    concept_names: Optional[str] = Query(None, description="概念板块名称列表（逗号分隔，如：人工智能,新能源）"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量，默认50"),
    sort_by: Optional[str] = Query("main_net_inflow", description="排序字段，如 main_net_inflow/main_inflow/main_outflow/turnover_rate/change_percent"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取资金流列表"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
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
    
    items, total = FundFlowService.get_fund_flow_list(
        db=db,
        target_date=target_date,
        stock_code=stock_code,
        concept_ids=concept_ids_list,
        concept_names=concept_names_list,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )
    
    # 将items转换为字典，添加concepts字段
    items_dict = []
    for item in items:
        item_dict = {
            column.name: getattr(item, column.name)
            for column in item.__table__.columns
        }
        # 添加概念板块
        if hasattr(item, '_concepts'):
            item_dict['concepts'] = [
                {"id": c.id, "name": c.name, "code": c.code}
                for c in item._concepts
            ]
        else:
            item_dict['concepts'] = []
        items_dict.append(item_dict)
    
    return {
        "items": items_dict,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size)
    }


@router.get("/{stock_code}/history")
def get_fund_flow_history(
    stock_code: str,
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取资金流历史"""
    start = parse_date(start_date)
    end = parse_date(end_date)
    if not start or not end:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    items = FundFlowService.get_fund_flow_history(db, stock_code, start, end)
    return items


@router.get("/concept")
def get_concept_fund_flow(
    date: str = Query(..., description="日期，格式YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=200, description="返回条数，默认50，最大200"),
    db: Session = Depends(get_db),
):
    """获取指定日期的概念资金流（仅查询库数据）"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")

    items = FundFlowService.get_concept_fund_flow_db(db, target_date, limit=limit)
    return items


@router.get("/industry")
def get_industry_fund_flow(
    date: str = Query(..., description="日期，格式YYYY-MM-DD"),
    limit: int = Query(200, ge=1, le=500, description="返回条数，默认200，最大500"),
    db: Session = Depends(get_db)
):
    """获取行业资金流（历史/当日），数据来自 daily sync 的 industry_fund_flow"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    items = FundFlowService.get_industry_fund_flow(db, target_date, limit=limit)
    return items

