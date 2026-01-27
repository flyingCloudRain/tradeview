"""
资金流筛选条件 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class DateRange(BaseModel):
    """日期范围"""
    start: Optional[date] = Field(None, description="开始日期")
    end: Optional[date] = Field(None, description="结束日期")


class NetInflowRange(BaseModel):
    """主力净流入区间"""
    min: Optional[float] = Field(None, description="最小值（单位：元），如 100000000 表示1亿")
    max: Optional[float] = Field(None, description="最大值（单位：元），如 10000000 表示1000万")


class LimitUpCountRange(BaseModel):
    """涨停次数区间"""
    min: Optional[int] = Field(None, description="最小涨停次数，如 1 表示至少涨停1次")
    max: Optional[int] = Field(None, description="最大涨停次数，如 5 表示最多涨停5次")


class DateRangeCondition(BaseModel):
    """日期范围筛选条件"""
    date_range: DateRange = Field(..., description="日期范围")
    main_net_inflow: Optional[NetInflowRange] = Field(None, description="主力净流入区间条件")
    limit_up_count: Optional[LimitUpCountRange] = Field(None, description="涨停次数区间条件")


class FundFlowFilterRequest(BaseModel):
    """资金流筛选请求"""
    conditions: List[DateRangeCondition] = Field(..., description="筛选条件列表，多个条件之间是AND关系")
    concept_ids: Optional[List[int]] = Field(None, description="概念板块ID列表（可选）")
    concept_names: Optional[List[str]] = Field(None, description="概念板块名称列表（可选）")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    sort_by: Optional[str] = Field("main_net_inflow", description="排序字段")
    order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")


class FundFlowFilterResponse(BaseModel):
    """资金流筛选响应"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    match_conditions: List[dict] = Field(..., description="匹配的条件详情")
    latest_date: Optional[date] = Field(None, description="最新数据日期")
    latest_main_net_inflow: Optional[float] = Field(None, description="最新主力净流入")
    concepts: Optional[List[dict]] = Field(None, description="概念板块列表")


class ConceptNetAmountRange(BaseModel):
    """概念净额区间"""
    min: Optional[float] = Field(None, description="最小净额（单位：元），如 100000000 表示1亿")
    max: Optional[float] = Field(None, description="最大净额（单位：元），如 10000000 表示1000万")


class ConceptInflowRange(BaseModel):
    """概念流入资金区间"""
    min: Optional[float] = Field(None, description="最小流入资金（单位：元）")
    max: Optional[float] = Field(None, description="最大流入资金（单位：元）")


class ConceptOutflowRange(BaseModel):
    """概念流出资金区间"""
    min: Optional[float] = Field(None, description="最小流出资金（单位：元）")
    max: Optional[float] = Field(None, description="最大流出资金（单位：元）")


class ConceptIndexChangeRange(BaseModel):
    """概念指数涨跌幅区间"""
    min: Optional[float] = Field(None, description="最小涨跌幅（单位：%）")
    max: Optional[float] = Field(None, description="最大涨跌幅（单位：%）")


class ConceptDateRangeCondition(BaseModel):
    """概念日期范围筛选条件"""
    date_range: Optional[DateRange] = Field(None, description="日期范围（可选）")
    net_amount: Optional[ConceptNetAmountRange] = Field(None, description="净额区间条件")
    inflow: Optional[ConceptInflowRange] = Field(None, description="流入资金区间条件")
    outflow: Optional[ConceptOutflowRange] = Field(None, description="流出资金区间条件")
    index_change_percent: Optional[ConceptIndexChangeRange] = Field(None, description="指数涨跌幅区间条件")
    stock_count: Optional[LimitUpCountRange] = Field(None, description="公司家数区间条件")


class ConceptFundFlowFilterRequest(BaseModel):
    """概念资金流筛选请求"""
    conditions: List[ConceptDateRangeCondition] = Field(..., description="筛选条件列表，多个条件之间是AND关系")
    concepts: Optional[List[str]] = Field(None, description="概念名称列表（可选，支持模糊匹配）")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=200, description="每页数量")
    sort_by: Optional[str] = Field("net_amount", description="排序字段：net_amount/inflow/outflow/index_change_percent/date")
    order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")
