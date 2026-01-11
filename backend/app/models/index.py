"""
大盘指数数据模型
"""
from sqlalchemy import Column, String, Date, Numeric, BigInteger
from datetime import date

from app.database.base import BaseModel


class IndexHistory(BaseModel):
    """大盘指数历史表"""
    __tablename__ = "index_history"
    
    date = Column(Date, nullable=False, index=True)
    index_code = Column(String(20), nullable=False, index=True)
    index_name = Column(String(50), nullable=False)
    close_price = Column(Numeric(10, 2))
    change_percent = Column(Numeric(5, 2))
    volume = Column(BigInteger)
    amount = Column(Numeric(15, 2))
    
    __table_args__ = (
        {"comment": "大盘指数历史表"},
    )

