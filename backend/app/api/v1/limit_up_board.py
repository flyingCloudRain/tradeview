"""
涨停板分析API路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import math

from app.database.session import get_db
from app.services.limit_up_board_service import LimitUpBoardService
from app.schemas.limit_up_board import (
    LimitUpBoardListResponse,
    LimitUpBoardResponse,
    LimitUpBoardCreate,
    LimitUpBoardUpdate,
    LimitUpBoardBatchCreate,
)
from app.utils.date_utils import parse_date
from app.config import settings

router = APIRouter()


@router.get("/", response_model=LimitUpBoardListResponse)
def get_limit_up_board_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD"),
    board_name: Optional[str] = Query(None, description="板块名称"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    stock_name: Optional[str] = Query(None, description="股票名称（模糊查询）"),
    tag: Optional[str] = Query(None, description="标签筛选（模糊查询）"),
    limit_up_reason: Optional[str] = Query(None, description="涨停原因筛选（模糊查询）"),
    concept_id: Optional[int] = Query(None, description="概念板块ID筛选"),
    concept_name: Optional[str] = Query(None, description="概念板块名称筛选"),
    db: Session = Depends(get_db)
):
    """获取涨停板分析列表"""
    target_date = None
    if date:
        target_date = parse_date(date)
        if not target_date:
            raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    items, total = LimitUpBoardService.get_list(
        db=db,
        page=page,
        page_size=page_size,
        target_date=target_date,
        board_name=board_name,
        stock_code=stock_code,
        stock_name=stock_name,
        tag=tag,
        limit_up_reason=limit_up_reason,
        concept_id=concept_id,
        concept_name=concept_name,
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return LimitUpBoardListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{item_id}", response_model=LimitUpBoardResponse)
def get_limit_up_board(
    item_id: int,
    db: Session = Depends(get_db)
):
    """根据ID获取涨停板分析"""
    item = LimitUpBoardService.get_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="涨停板分析记录不存在")
    return item


@router.post("/", response_model=LimitUpBoardResponse)
def create_limit_up_board(
    item: LimitUpBoardCreate,
    auto_extract_concepts: bool = Query(True, description="是否自动从关键字提取概念板块"),
    db: Session = Depends(get_db)
):
    """创建涨停板分析"""
    return LimitUpBoardService.create(db, item, auto_extract_concepts)


@router.post("/batch", response_model=dict)
def batch_create_limit_up_board(
    batch_data: LimitUpBoardBatchCreate = Body(...),
    db: Session = Depends(get_db)
):
    """批量创建涨停板分析"""
    # 批量创建
    items = LimitUpBoardService.batch_create(
        db,
        batch_data.items,
        batch_data.auto_extract_concepts
    )
    
    return {
        "message": "批量创建成功",
        "date": batch_data.date.strftime("%Y-%m-%d"),
        "count": len(items)
    }


@router.patch("/{item_id}", response_model=LimitUpBoardResponse)
def update_limit_up_board(
    item_id: int,
    item_update: LimitUpBoardUpdate,
    db: Session = Depends(get_db)
):
    """更新涨停板分析"""
    item = LimitUpBoardService.update(db, item_id, item_update)
    if not item:
        raise HTTPException(status_code=404, detail="涨停板分析记录不存在")
    return item


@router.delete("/{item_id}", response_model=dict)
def delete_limit_up_board(
    item_id: int,
    db: Session = Depends(get_db)
):
    """删除涨停板分析"""
    success = LimitUpBoardService.delete(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="涨停板分析记录不存在")
    return {"message": "删除成功"}


@router.delete("/date/{date_str}", response_model=dict)
def delete_limit_up_board_by_date(
    date_str: str,
    db: Session = Depends(get_db)
):
    """根据日期删除涨停板分析"""
    target_date = parse_date(date_str)
    if not target_date:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    deleted_count = LimitUpBoardService.delete_by_date(db, target_date)
    return {
        "message": "删除成功",
        "date": date_str,
        "deleted_count": deleted_count
    }


@router.get("/statistics/board", response_model=dict)
def get_board_statistics(
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """获取板块统计信息"""
    target_date = None
    if date:
        target_date = parse_date(date)
        if not target_date:
            raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    
    return LimitUpBoardService.get_board_statistics(db, target_date)
