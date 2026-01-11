"""
龙虎榜Pydantic模式
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class LhbDetailBase(BaseModel):
    """龙虎榜详情基础模式"""
    date: date
    stock_code: str
    stock_name: str
    close_price: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    net_buy_amount: Optional[Decimal] = None
    buy_amount: Optional[Decimal] = None
    sell_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    turnover_rate: Optional[Decimal] = None
    concept: Optional[str] = None


class LhbInstitutionResponse(BaseModel):
    """机构明细响应"""
    id: int
    institution_name: Optional[str] = None
    buy_amount: Optional[Decimal] = None
    sell_amount: Optional[Decimal] = None
    net_buy_amount: Optional[Decimal] = None
    flag: Optional[str] = None  # 交易方向：买入/卖出
    
    class Config:
        from_attributes = True


class LhbDetailResponse(LhbDetailBase):
    """龙虎榜详情响应"""
    id: int
    created_at: datetime
    # 聚合的机构信息（用于列表显示）
    institutions_summary: Optional[str] = None  # 主要机构名称，用逗号分隔（已废弃，使用institutions）
    # 机构明细列表（按净买额倒序）
    institutions: List[LhbInstitutionResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class LhbListResponse(BaseModel):
    """龙虎榜列表响应"""
    items: List[LhbDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LhbDetailFullResponse(BaseModel):
    """龙虎榜完整详情响应"""
    detail: LhbDetailResponse
    institutions: List[LhbInstitutionResponse] = Field(default_factory=list)


class LhbHotInstitutionResponse(BaseModel):
    """龙虎榜机构游资榜响应"""
    id: int
    date: date
    institution_name: str
    institution_code: Optional[str] = None
    buy_stock_count: Optional[int] = None
    sell_stock_count: Optional[int] = None
    buy_amount: Optional[Decimal] = None
    sell_amount: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    buy_stocks: Optional[str] = None
    
    class Config:
        from_attributes = True


class LhbInstitutionItemResponse(BaseModel):
    """机构榜明细响应（直接从lhb_institution表）"""
    id: int
    date: date
    institution_name: Optional[str] = None
    stock_code: str
    stock_name: Optional[str] = None  # 从lhb_detail关联获取
    flag: Optional[str] = None  # 操作方向：买入/卖出
    buy_amount: Optional[float] = None
    sell_amount: Optional[float] = None
    net_buy_amount: Optional[float] = None
    
    class Config:
        from_attributes = True


class LhbHotListResponse(BaseModel):
    """龙虎榜机构游资榜列表响应"""
    items: List[LhbInstitutionItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LhbHotInstitutionDetailResponse(BaseModel):
    """营业部买入股票明细（来自 stock_lhb_yyb_detail_em）"""
    date: date
    stock_code: str
    stock_name: str
    change_percent: Optional[Decimal] = None
    buy_amount: Optional[Decimal] = None
    sell_amount: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    reason: Optional[str] = None
    after_1d: Optional[Decimal] = None
    after_2d: Optional[Decimal] = None
    after_3d: Optional[Decimal] = None
    after_5d: Optional[Decimal] = None
    after_10d: Optional[Decimal] = None
    after_20d: Optional[Decimal] = None
    after_30d: Optional[Decimal] = None


class TraderBranchResponse(BaseModel):
    """游资-营业部映射（支路）"""
    id: int
    trader_id: int
    institution_name: str
    institution_code: Optional[str] = None
    
    class Config:
        from_attributes = True


class TraderResponse(BaseModel):
    """游资主体及其营业部列表（极简）"""
    id: int
    name: str
    aka: Optional[str] = None
    branches: List[TraderBranchResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True

