"""
活跃机构（游资）数据模型
"""
from sqlalchemy import Column, String, Date, Numeric
from datetime import date

from app.database.base import BaseModel


class CapitalDetail(BaseModel):
    """活跃机构详情表"""
    __tablename__ = "capital_detail"
    
    date = Column(Date, nullable=False, index=True)
    capital_name = Column(String(100), nullable=False, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    buy_amount = Column(Numeric(15, 2))
    sell_amount = Column(Numeric(15, 2))
    net_buy_amount = Column(Numeric(15, 2))
    
    __table_args__ = (
        {"comment": "活跃机构详情表"},
    )

