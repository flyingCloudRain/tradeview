"""
活跃机构API路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.database.session import get_db
from app.services.capital_service import CapitalService
from app.utils.date_utils import parse_date
from app.config import settings

router = APIRouter()


@router.get("/")
def get_capital_list(
    date: str = Query(..., description="日期"),
    capital_name: Optional[str] = Query(None, description="游资名称"),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    db: Session = Depends(get_db)
):
    """获取活跃机构列表"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    items, total = CapitalService.get_capital_list(
        db, target_date, capital_name, page, page_size
    )
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size)
    }


@router.get("/{capital_name}")
def get_capital_detail(
    capital_name: str,
    date: str = Query(..., description="日期"),
    db: Session = Depends(get_db)
):
    """获取活跃机构详情"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    items = CapitalService.get_capital_detail(db, capital_name, target_date)
    return items

