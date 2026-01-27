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


class LhbStockStatisticsItem(BaseModel):
    """龙虎榜个股统计项"""
    stock_code: str
    stock_name: str
    appear_count: int  # 上榜次数
    total_net_buy_amount: float  # 净流入总额
    total_buy_amount: float  # 买入总额
    total_sell_amount: float  # 卖出总额
    first_date: Optional[date] = None  # 首次上榜日期
    last_date: Optional[date] = None  # 最后上榜日期


class LhbStockStatisticsResponse(BaseModel):
    """龙虎榜个股统计响应"""
    items: List[LhbStockStatisticsItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    start_date: date
    end_date: date


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


class InstitutionTradingStatisticsResponse(BaseModel):
    """机构交易统计响应"""
    id: int
    date: date
    stock_code: str
    stock_name: str
    close_price: Optional[float] = None
    change_percent: Optional[float] = None
    institution_net_buy_amount: Optional[float] = None  # 机构买入净额
    buyer_institution_count: Optional[int] = None
    seller_institution_count: Optional[int] = None
    institution_buy_amount: Optional[float] = None
    institution_sell_amount: Optional[float] = None
    market_total_amount: Optional[float] = None
    net_buy_ratio: Optional[float] = None
    turnover_rate: Optional[float] = None
    circulation_market_value: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class InstitutionTradingStatisticsListResponse(BaseModel):
    """机构交易统计列表响应"""
    items: List[InstitutionTradingStatisticsResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class InstitutionTradingStatisticsAggregatedItem(BaseModel):
    """机构交易统计聚合项"""
    stock_code: str
    stock_name: str
    appear_count: int  # 上榜次数
    total_buy_amount: Optional[float] = None  # 累计买入金额
    total_sell_amount: Optional[float] = None  # 累计卖出金额
    total_net_buy_amount: Optional[float] = None  # 累计净买入金额
    total_market_amount: Optional[float] = None  # 累计市场总成交额
    net_buy_ratio: Optional[float] = None  # 机构净买额占总成交额比（%）
    avg_close_price: Optional[float] = None  # 平均收盘价
    avg_circulation_market_value: Optional[float] = None  # 平均流通市值
    avg_turnover_rate: Optional[float] = None  # 平均换手率
    max_change_percent: Optional[float] = None  # 最大涨跌幅
    min_change_percent: Optional[float] = None  # 最小涨跌幅
    earliest_date: date  # 最早日期
    latest_date: date  # 最晚日期


class InstitutionTradingStatisticsAggregatedResponse(BaseModel):
    """机构交易统计聚合响应"""
    items: List[InstitutionTradingStatisticsAggregatedItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ActiveBranchResponse(BaseModel):
    """活跃营业部响应"""
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
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActiveBranchListResponse(BaseModel):
    """活跃营业部列表响应"""
    items: List[ActiveBranchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ActiveBranchDetailResponse(BaseModel):
    """活跃营业部交易详情响应"""
    id: int
    institution_code: str
    institution_name: Optional[str] = None
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
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActiveBranchDetailStatistics(BaseModel):
    """活跃营业部交易详情统计"""
    buy_branch_count: int  # 买入营业部个数
    sell_branch_count: int  # 卖出营业部个数
    total_buy_amount: float  # 买入总金额
    total_sell_amount: float  # 卖出总金额


class ActiveBranchDetailListResponse(BaseModel):
    """活跃营业部交易详情列表响应"""
    items: List[ActiveBranchDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    statistics: Optional[ActiveBranchDetailStatistics] = None  # 统计信息


class BuyStockStatisticsItem(BaseModel):
    """买入股票统计项"""
    stock_name: str  # 股票名称
    appear_count: int  # 出现次数
    buy_branch_count: int = 0  # 买入营业部数
    sell_branch_count: int = 0  # 卖出营业部数
    net_buy_amount: float = 0.0  # 净买入额
    net_sell_amount: float = 0.0  # 净卖出额


class BuyStockStatisticsResponse(BaseModel):
    """买入股票统计响应"""
    items: List[BuyStockStatisticsItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    date: date  # 统计日期


class BuyStockBranchesResponse(BaseModel):
    """买入股票对应的营业部列表响应"""
    items: List[ActiveBranchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    stock_name: str  # 股票名称
    date: date  # 统计日期

