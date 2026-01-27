"""
股票历史行情数据模型
"""
from sqlalchemy import Column, String, Date, Numeric, Index, BigInteger
from datetime import date

from app.database.base import BaseModel


class StockHistory(BaseModel):
    """股票历史行情表"""
    __tablename__ = "stock_history"
    
    date = Column(Date, nullable=False, index=True, comment="日期")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    stock_name = Column(String(50), nullable=True, comment="股票名称")
    open_price = Column(Numeric(10, 2), nullable=True, comment="开盘价")
    close_price = Column(Numeric(10, 2), nullable=True, comment="收盘价")
    high_price = Column(Numeric(10, 2), nullable=True, comment="最高价")
    low_price = Column(Numeric(10, 2), nullable=True, comment="最低价")
    volume = Column(BigInteger, nullable=True, comment="成交量")
    amount = Column(Numeric(20, 2), nullable=True, comment="成交额")
    amplitude = Column(Numeric(5, 2), nullable=True, comment="振幅")
    change_percent = Column(Numeric(8, 2), nullable=True, comment="涨跌幅")
    change_amount = Column(Numeric(10, 2), nullable=True, comment="涨跌额")
    turnover_rate = Column(Numeric(5, 2), nullable=True, comment="换手率")
    
    __table_args__ = (
        Index('idx_stock_history_date_stock', 'date', 'stock_code'),
        Index('idx_stock_history_stock_date', 'stock_code', 'date'),
        {"comment": "股票历史行情表"},
    )
