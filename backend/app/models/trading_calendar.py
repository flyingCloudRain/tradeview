"""
交易日历数据模型
"""
from sqlalchemy import Column, String, Date, Text, JSON, Numeric, Boolean
from datetime import date

from app.database.base import BaseModel


class TradingCalendar(BaseModel):
    """交易日历表"""
    __tablename__ = "trading_calendar"
    
    date = Column(Date, nullable=False, index=True, comment="交易日期")
    stock_name = Column(String(50), nullable=False, comment="股票名称")
    direction = Column(String(10), nullable=False, comment="操作方向：买入/卖出")
    strategy = Column(String(20), nullable=False, comment="策略：低吸/排板")
    price = Column(Numeric(10, 2), nullable=True, comment="价格")
    is_executed = Column(Boolean, nullable=True, default=False, comment="是否执行策略")
    source = Column(String(100), nullable=True, comment="来源")
    notes = Column(Text, nullable=True, comment="备注")
    images = Column(JSON, nullable=True, comment="图片URL列表")
    
    __table_args__ = (
        {"comment": "交易日历表"},
    )

