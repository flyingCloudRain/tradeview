"""
跌停池API路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.database.session import get_db
from app.services.zt_pool_service import ZtPoolDownService
from app.schemas.zt_pool import ZtPoolListResponse
from app.utils.date_utils import parse_date
from app.config import settings

router = APIRouter()


@router.get("/", response_model=ZtPoolListResponse)
def get_zt_pool_down_list(
    date: str = Query(..., description="日期，格式：YYYY-MM-DD"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    concept: Optional[str] = Query(None, description="概念筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    consecutive_limit_count: Optional[int] = Query(None, description="连板/连跌数筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="排序方向，默认升序（跌幅在前）"),
    db: Session = Depends(get_db)
):
    """获取跌停池列表"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")

    items, total = ZtPoolDownService.get_list(
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

    total_pages = math.ceil(total / page_size) if page_size else 0

    return ZtPoolListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

