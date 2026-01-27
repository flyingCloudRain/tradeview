"""
股票概念板块Pydantic模式
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StockConceptBase(BaseModel):
    """概念板块基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="概念板块名称")
    code: Optional[str] = Field(None, max_length=20, description="概念板块代码")
    description: Optional[str] = Field(None, description="概念板块描述")
    parent_id: Optional[int] = Field(None, description="父概念ID，NULL表示一级概念")
    level: int = Field(1, ge=1, le=3, description="层级：1=一级，2=二级，3=三级")
    sort_order: int = Field(0, description="同级排序顺序")


class StockConceptCreate(StockConceptBase):
    """创建概念板块"""
    pass


class StockConceptUpdate(BaseModel):
    """更新概念板块"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class StockConceptResponse(StockConceptBase):
    """概念板块响应"""
    id: int
    path: Optional[str] = Field(None, description="层级路径")
    stock_count: int = Field(0, description="关联的个股数量")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ConceptInfo(BaseModel):
    """概念信息（带层级，用于个股响应）"""
    id: int
    name: str
    code: Optional[str] = None
    level: int = Field(..., description="层级：1=一级，2=二级，3=三级")
    parent_id: Optional[int] = Field(None, description="父概念ID")
    path: Optional[str] = Field(None, description="层级路径")
    
    class Config:
        from_attributes = True


class StockConceptTree(StockConceptResponse):
    """带子节点的树形结构"""
    children: List['StockConceptTree'] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class StockConceptListResponse(BaseModel):
    """概念板块列表响应"""
    items: List[StockConceptResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StockConceptMappingRequest(BaseModel):
    """股票概念关联请求"""
    stock_name: str = Field(..., min_length=1, max_length=50, description="股票名称")
    concept_ids: List[int] = Field(..., min_items=0, description="概念板块ID列表")


class StockConceptMappingResponse(BaseModel):
    """股票概念关联响应"""
    stock_name: str
    concepts: List[StockConceptResponse]


class BatchStockConceptMappingRequest(BaseModel):
    """批量查询股票概念关联请求"""
    stock_names: List[str] = Field(..., min_items=0, description="股票名称列表")


class BatchStockConceptMappingResponse(BaseModel):
    """批量查询股票概念关联响应"""
    mappings: dict[str, List[StockConceptResponse]]  # 股票名称 -> 概念板块列表
