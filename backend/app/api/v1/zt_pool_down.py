"""
跌停池API路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.database.session import get_db
from app.services.zt_pool_service import ZtPoolDownService
from app.schemas.zt_pool import ZtPoolListResponse
from app.utils.date_utils import parse_date, get_trading_date
from app.config import settings

router = APIRouter()


@router.get("/", response_model=ZtPoolListResponse)
def get_zt_pool_down_list(
    date: Optional[str] = Query(None, description="日期（单日期查询，可选，与日期范围查询互斥）"),
    start_date: Optional[str] = Query(None, description="开始日期（日期范围查询，可选）"),
    end_date: Optional[str] = Query(None, description="结束日期（日期范围查询，可选）"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    stock_name: Optional[str] = Query(None, description="股票名称（模糊匹配）"),
    concept: Optional[str] = Query(None, description="概念筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    consecutive_limit_count: Optional[int] = Query(None, description="连板/连跌数筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    order: str = Query("asc", pattern="^(asc|desc)$", description="排序方向，默认升序（跌幅在前）"),
    db: Session = Depends(get_db)
):
    """
    获取跌停池列表
    
    支持两种查询模式：
    1. 单日期查询：使用 date 参数
    2. 日期范围查询：使用 start_date 和 end_date 参数
    
    如果都没有提供，默认查询当日数据
    """
    # 确定查询日期范围
    if start_date and end_date:
        # 日期范围查询
        start = parse_date(start_date)
        end = parse_date(end_date)
        if not start or not end:
            raise HTTPException(status_code=400, detail="日期格式错误")
        if start > end:
            raise HTTPException(status_code=400, detail="开始日期不能大于结束日期")
        target_date = None  # 使用日期范围
    elif date:
        # 单日期查询（保持向后兼容）
        target_date = parse_date(date)
        if not target_date:
            raise HTTPException(status_code=400, detail="日期格式错误")
        start = None
        end = None
    else:
        # 默认查询当日
        target_date = get_trading_date()
        if not target_date:
            raise HTTPException(status_code=404, detail="未找到可用的交易日期")
        start = None
        end = None
    
    # 根据查询模式调用不同的服务方法
    if target_date is not None:
        # 单日期查询
        items, total = ZtPoolDownService.get_list(
            db=db,
            target_date=target_date,
            stock_code=stock_code,
            stock_name=stock_name,
            concept=concept,
            industry=industry,
            consecutive_limit_count=consecutive_limit_count,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order
        )
    else:
        # 日期范围查询
        items, total = ZtPoolDownService.get_list_by_date_range(
            db=db,
            start_date=start,
            end_date=end,
            stock_code=stock_code,
            stock_name=stock_name,
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

