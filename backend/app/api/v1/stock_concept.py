"""
股票概念板块API路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from app.database.session import get_db
from app.services.stock_concept_service import StockConceptService, StockConceptMappingService
from app.models.stock_concept import StockConcept
from app.schemas.stock_concept import (
    StockConceptCreate,
    StockConceptUpdate,
    StockConceptResponse,
    StockConceptListResponse,
    StockConceptTree,
    ConceptInfo,
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
    level: Optional[int] = Query(None, ge=1, le=3, description="层级筛选：1=一级，2=二级，3=三级"),
    parent_id: Optional[int] = Query(None, description="父概念ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取概念板块列表"""
    items, total = StockConceptService.get_list(
        db=db,
        name=name,
        code=code,
        level=level,
        parent_id=parent_id,
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


@router.get("/tree", response_model=List[StockConceptTree])
def get_concept_tree(
    max_level: int = Query(3, ge=1, le=3, description="最大层级深度"),
    db: Session = Depends(get_db)
):
    """获取概念树形结构"""
    def build_tree_node(concept: StockConcept, current_level: int) -> StockConceptTree:
        """递归构建树节点"""
        node = StockConceptTree.model_validate(concept)
        
        if current_level < max_level:
            # 查询子概念
            children = db.query(StockConcept).filter(
                StockConcept.parent_id == concept.id
            ).order_by(
                StockConcept.sort_order.asc(),
                StockConcept.name.asc()
            ).all()
            
            node.children = [build_tree_node(child, current_level + 1) for child in children]
        
        return node
    
    # 查询所有一级概念
    level1_concepts = StockConceptService.get_tree(db, max_level)
    
    return [build_tree_node(concept, 1) for concept in level1_concepts]


@router.get("/{concept_id}/ancestors", response_model=List[StockConceptResponse])
def get_concept_ancestors(
    concept_id: int,
    db: Session = Depends(get_db)
):
    """获取概念的所有祖先概念（向上查询）"""
    concept = StockConceptService.get_by_id(db, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="概念板块不存在")
    
    ancestors = concept.get_all_ancestors()
    return ancestors


@router.get("/{concept_id}/descendants", response_model=List[StockConceptResponse])
def get_concept_descendants(
    concept_id: int,
    include_self: bool = Query(False, description="是否包含自身"),
    db: Session = Depends(get_db)
):
    """获取概念的所有后代概念（向下查询）"""
    concept = StockConceptService.get_by_id(db, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="概念板块不存在")
    
    descendants = concept.get_all_descendants()
    if include_self:
        descendants.insert(0, concept)
    
    return descendants


@router.get("/{concept_id}/stocks", response_model=List[str])
def get_concept_stocks(
    concept_id: int,
    include_descendants: bool = Query(True, description="是否包含子概念的个股"),
    db: Session = Depends(get_db)
):
    """获取概念关联的所有个股（可包含子概念）"""
    concept = StockConceptService.get_by_id(db, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="概念板块不存在")
    
    # 扩展概念ID
    if include_descendants:
        concept_ids = StockConceptService.expand_concept_ids(
            db=db,
            concept_ids=[concept_id],
            include_descendants=True
        )
    else:
        concept_ids = [concept_id]
    
    # 查询关联的股票名称
    from app.models.stock_concept import StockConceptMapping
    stock_names = db.query(StockConceptMapping.stock_name).distinct().filter(
        StockConceptMapping.concept_id.in_(concept_ids)
    ).all()
    
    return [row[0] for row in stock_names]


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
    level: Optional[int] = Query(None, ge=1, le=3, description="按层级筛选"),
    db: Session = Depends(get_db)
):
    """获取股票的概念板块列表（包含层级信息）"""
    concepts = StockConceptService.get_stock_concepts_with_hierarchy(db, stock_name)
    
    # 按层级筛选
    if level is not None:
        concepts = [c for c in concepts if c.level == level]
    
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


@router.post("/{concept_id}/stocks", response_model=StockConceptResponse)
def add_stock_to_concept(
    concept_id: int,
    stock_name: str = Query(..., description="股票名称"),
    db: Session = Depends(get_db)
):
    """为概念添加个股"""
    concept = StockConceptService.get_by_id(db, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="概念板块不存在")
    
    # 只有2级和3级概念可以添加个股
    if concept.level < 2:
        raise HTTPException(status_code=400, detail="只有2级和3级概念可以添加个股")
    
    try:
        StockConceptMappingService.add_concept_to_stock(
            db=db,
            stock_name=stock_name.strip(),
            concept_id=concept_id
        )
        # 更新stock_count
        from app.models.stock_concept import StockConceptMapping
        stock_count = db.query(StockConceptMapping).filter(
            StockConceptMapping.concept_id == concept_id
        ).count()
        concept.stock_count = stock_count
        db.commit()
        db.refresh(concept)
        return concept
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"添加个股失败: {str(e)}")


@router.delete("/{concept_id}/stocks/{stock_name}", status_code=204)
def remove_stock_from_concept(
    concept_id: int,
    stock_name: str,
    db: Session = Depends(get_db)
):
    """从概念移除个股"""
    concept = StockConceptService.get_by_id(db, concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="概念板块不存在")
    
    success = StockConceptMappingService.remove_concept_from_stock(
        db=db,
        stock_name=stock_name,
        concept_id=concept_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="关联关系不存在")
    
    # 更新stock_count
    from app.models.stock_concept import StockConceptMapping
    stock_count = db.query(StockConceptMapping).filter(
        StockConceptMapping.concept_id == concept_id
    ).count()
    concept.stock_count = stock_count
    db.commit()
    
    return None
