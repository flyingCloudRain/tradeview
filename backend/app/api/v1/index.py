"""
大盘指数API路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.database.session import get_db
from app.services.index_service import IndexService
from app.utils.date_utils import parse_date
from app.schemas.index import IndexResponse

router = APIRouter()


@router.get("/", response_model=List[IndexResponse])
def get_index_list(
    date: str = Query(..., description="日期"),
    index_code: Optional[str] = Query(None, description="指数代码"),
    db: Session = Depends(get_db)
):
    """获取指数列表（包含成交量变化比例）"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    items = IndexService.get_index_list(db, target_date, index_code)
    return items


@router.get("/{index_code}/history")
def get_index_history(
    index_code: str,
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取指数历史数据"""
    start = parse_date(start_date)
    end = parse_date(end_date)
    if not start or not end:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    items = IndexService.get_index_history(db, index_code, start, end)
    return items

