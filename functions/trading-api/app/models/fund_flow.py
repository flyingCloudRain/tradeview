"""
个股资金流数据模型
"""
from sqlalchemy import Column, String, Date, Numeric, Boolean
from datetime import date

from app.database.base import BaseModel


class StockFundFlow(BaseModel):
    """个股资金流表"""
    __tablename__ = "stock_fund_flow"
    
    date = Column(Date, nullable=False, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    current_price = Column(Numeric(12, 2))
    change_percent = Column(Numeric(8, 2))
    turnover_rate = Column(Numeric(5, 2))
    main_inflow = Column(Numeric(15, 2))
    main_outflow = Column(Numeric(15, 2))
    main_net_inflow = Column(Numeric(15, 2))
    turnover_amount = Column(Numeric(20, 2))
    is_limit_up = Column(Boolean, default=False, comment="是否涨停")
    is_lhb = Column(Boolean, default=False, comment="是否龙虎榜")
    
    __table_args__ = (
        {"comment": "个股资金流表"},
    )


class IndustryFundFlow(BaseModel):
    """行业/概念资金流（接口 stock_fund_flow_industry）"""
    __tablename__ = "industry_fund_flow"
    
    date = Column(Date, nullable=False, index=True)
    industry = Column(String(100), nullable=False, index=True)
    index_value = Column(Numeric(12, 2))
    index_change_percent = Column(Numeric(8, 2))
    inflow = Column(Numeric(16, 2))
    outflow = Column(Numeric(16, 2))
    net_amount = Column(Numeric(16, 2))
    stock_count = Column(Numeric(10, 0))
    leader_stock = Column(String(100))
    leader_change_percent = Column(Numeric(8, 2))
    leader_price = Column(Numeric(12, 2))
    
    __table_args__ = (
        {"comment": "行业/概念资金流表（stock_fund_flow_industry 即时）"},
    )


class ConceptFundFlow(BaseModel):
    """概念资金流（接口 stock_fund_flow_concept）"""
    __tablename__ = "concept_fund_flow"

    date = Column(Date, nullable=False, index=True)
    concept = Column(String(200), nullable=False, index=True)
    index_value = Column(Numeric(12, 2))
    index_change_percent = Column(Numeric(8, 2))
    inflow = Column(Numeric(16, 2))
    outflow = Column(Numeric(16, 2))
    net_amount = Column(Numeric(16, 2))
    stock_count = Column(Numeric(10, 0))
    leader_stock = Column(String(100))
    leader_change_percent = Column(Numeric(8, 2))
    leader_price = Column(Numeric(12, 2))

    __table_args__ = (
        {"comment": "概念资金流表（stock_fund_flow_concept 即时）"},
    )

