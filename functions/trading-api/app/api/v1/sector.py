"""
概念板块API路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database.session import get_db
from app.services.sector_service import SectorService
from app.utils.date_utils import parse_date

router = APIRouter()


@router.get("/")
def get_sector_list(
    date: str = Query(..., description="日期"),
    sector_code: Optional[str] = Query(None, description="板块代码"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取板块列表"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    items = SectorService.get_sector_list(db, target_date, sector_code, sort_by, order)
    return items


@router.get("/{sector_code}")
def get_sector_detail(
    sector_code: str,
    date: str = Query(..., description="日期"),
    db: Session = Depends(get_db)
):
    """获取板块详情"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    item = SectorService.get_sector_detail(db, sector_code, target_date)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="未找到数据")
    
    return item

