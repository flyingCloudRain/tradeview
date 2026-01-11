"""
股票概念板块API路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from app.database.session import get_db
from app.services.stock_concept_service import StockConceptService, StockConceptMappingService
from app.schemas.stock_concept import (
    StockConceptCreate,
    StockConceptUpdate,
    StockConceptResponse,
    StockConceptListResponse,
    StockConceptMappingRequest,
    StockConceptMappingResponse,
    BatchStockConceptMappingRequest,
    BatchStockConceptMappingResponse,
)
from app.config import settings

router = APIRouter()


@router.get("/", response_model=StockConceptListResponse)
def get_stock_concepts(
    name: Optional[str] = Query(None, description="概念板块名称（模糊搜索）"),
    code: Optional[str] = Query(None, description="概念板块代码（精确搜索）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取概念板块列表"""
    items, total = StockConceptService.get_list(
        db=db,
        name=name,
        code=code,
        page=page,
        page_size=page_size,
    )
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    return StockConceptListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{concept_id}", response_model=StockConceptResponse)
def get_stock_concept(
    concept_id: int,
    db: Session = Depends(get_db)
):
    """获取概念板块详情"""
    concept = StockConceptService.get_by_id(db, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="概念板块不存在")
    return concept


@router.post("/", response_model=StockConceptResponse, status_code=201)
def create_stock_concept(
    concept_data: StockConceptCreate,
    db: Session = Depends(get_db)
):
    """创建概念板块"""
    # 检查名称是否已存在
    existing = StockConceptService.get_by_name(db, concept_data.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"概念板块名称 '{concept_data.name}' 已存在")
    
    try:
        concept = StockConceptService.create(db, concept_data.model_dump())
        return concept
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")


@router.put("/{concept_id}", response_model=StockConceptResponse)
def update_stock_concept(
    concept_id: int,
    concept_data: StockConceptUpdate,
    db: Session = Depends(get_db)
):
    """更新概念板块"""
    # 如果更新名称，检查是否与其他记录冲突
    if concept_data.name:
        existing = StockConceptService.get_by_name(db, concept_data.name)
        if existing and existing.id != concept_id:
            raise HTTPException(status_code=400, detail=f"概念板块名称 '{concept_data.name}' 已存在")
    
    update_dict = {k: v for k, v in concept_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="没有提供更新数据")
    
    concept = StockConceptService.update(db, concept_id, update_dict)
    if not concept:
        raise HTTPException(status_code=404, detail="概念板块不存在")
    return concept


@router.delete("/{concept_id}", status_code=204)
def delete_stock_concept(
    concept_id: int,
    db: Session = Depends(get_db)
):
    """删除概念板块"""
    success = StockConceptService.delete(db, concept_id)
    if not success:
        raise HTTPException(status_code=404, detail="概念板块不存在")
    return None


# 股票概念关联API
@router.post("/mapping", response_model=StockConceptMappingResponse, status_code=201)
def set_stock_concepts(
    mapping_data: StockConceptMappingRequest,
    db: Session = Depends(get_db)
):
    """为股票设置概念板块（替换所有现有关联）"""
    concepts = StockConceptMappingService.set_concepts_for_stock(
        db=db,
        stock_name=mapping_data.stock_name,
        concept_ids=mapping_data.concept_ids
    )
    
    return StockConceptMappingResponse(
        stock_name=mapping_data.stock_name,
        concepts=concepts
    )


@router.get("/mapping/{stock_name}", response_model=StockConceptMappingResponse)
def get_stock_concepts(
    stock_name: str,
    db: Session = Depends(get_db)
):
    """获取股票的概念板块列表"""
    concepts = StockConceptMappingService.get_stock_concepts(db, stock_name)
    return StockConceptMappingResponse(
        stock_name=stock_name,
        concepts=concepts
    )


@router.put("/mapping/{stock_name}", response_model=StockConceptMappingResponse)
def update_stock_concepts(
    stock_name: str,
    concept_ids: List[int],
    db: Session = Depends(get_db)
):
    """更新股票的概念板块（替换所有现有关联）"""
    concepts = StockConceptMappingService.set_concepts_for_stock(
        db=db,
        stock_name=stock_name,
        concept_ids=concept_ids
    )
    
    return StockConceptMappingResponse(
        stock_name=stock_name,
        concepts=concepts
    )


@router.post("/mapping/batch", response_model=BatchStockConceptMappingResponse)
def batch_get_stock_concepts(
    request: BatchStockConceptMappingRequest,
    db: Session = Depends(get_db)
):
    """批量查询股票的概念板块"""
    mappings = StockConceptService.get_by_stock_names(db, request.stock_names)
    
    # 转换为响应格式
    result = {}
    for stock_name, concepts in mappings.items():
        result[stock_name] = concepts
    
    return BatchStockConceptMappingResponse(mappings=result)


@router.delete("/mapping/{stock_name}/{concept_id}", status_code=204)
def remove_stock_concept(
    stock_name: str,
    concept_id: int,
    db: Session = Depends(get_db)
):
    """从股票移除概念板块"""
    success = StockConceptMappingService.remove_concept_from_stock(
        db=db,
        stock_name=stock_name,
        concept_id=concept_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="关联关系不存在")
    return None
