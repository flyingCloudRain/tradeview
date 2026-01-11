"""
涨停池API路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import math

from app.database.session import get_db
from app.services.zt_pool_service import ZtPoolService
from app.schemas.zt_pool import ZtPoolListResponse, ZtPoolAnalysisResponse, ZtPoolUpdateRequest
from app.utils.date_utils import parse_date, get_trading_date
from app.config import settings

router = APIRouter()


@router.get("/", response_model=ZtPoolListResponse)
def get_zt_pool_list(
    date: str = Query(..., description="日期，格式：YYYY-MM-DD"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    concept: Optional[str] = Query(None, description="概念筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    consecutive_limit_count: Optional[int] = Query(None, description="连板数筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取涨停池列表"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    items, total = ZtPoolService.get_zt_pool_list(
        db=db,
        target_date=target_date,
        stock_code=stock_code,
        concept=concept,
        industry=industry,
        consecutive_limit_count=consecutive_limit_count,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order
    )
    
    total_pages = math.ceil(total / page_size)
    
    return ZtPoolListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.patch("/{record_id}", response_model=None)
def update_zt_pool_record(
    record_id: int,
    payload: ZtPoolUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新涨停池可编辑字段（概念、涨停原因）"""
    updated = ZtPoolService.update_fields(
        db=db,
        record_id=record_id,
        concept=payload.concept,
        limit_up_reason=payload.limit_up_reason,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"success": True}


@router.get("/analysis", response_model=ZtPoolAnalysisResponse)
def get_zt_analysis(
    date: str = Query(..., description="日期"),
    db: Session = Depends(get_db)
):
    """获取涨停分析"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    analysis = ZtPoolService.get_zt_analysis(db, target_date)
    return analysis


@router.get("/concepts", response_model=list[str])
def get_concept_list(
    date: Optional[str] = Query(None, description="日期，可选；不传则返回所有历史概念"),
    db: Session = Depends(get_db)
):
    """获取概念列表"""
    if date:
        target_date = parse_date(date)
        if not target_date:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="日期格式错误")
        concepts = ZtPoolService.get_concept_list(db, target_date)
    else:
        # 获取所有历史概念
        concepts = ZtPoolService.get_all_concepts(db)
    return concepts


@router.post("/sync")
def sync_zt_pool(
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD；默认当日交易日"),
    db: Session = Depends(get_db),
):
    """
    手动同步涨停股票池，使用 akshare 接口 stock_zt_pool_em
    """
    target_date = parse_date(date) if date else get_trading_date()
    if not target_date:
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    success = ZtPoolService.sync_data(db, target_date)
    if not success:
        raise HTTPException(status_code=500, detail="同步失败，可能无数据或接口异常")
    
    return {"success": True, "date": target_date}

