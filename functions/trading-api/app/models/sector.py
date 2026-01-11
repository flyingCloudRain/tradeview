"""
概念板块数据模型
"""
from sqlalchemy import Column, String, Date, Numeric, Integer
from datetime import date

from app.database.base import BaseModel


class SectorHistory(BaseModel):
    """概念板块历史表"""
    __tablename__ = "sector_history"
    
    date = Column(Date, nullable=False, index=True)
    sector_code = Column(String(20), nullable=False, index=True)
    sector_name = Column(String(50), nullable=False)
    change_percent = Column(Numeric(5, 2))
    rise_count = Column(Integer)
    fall_count = Column(Integer)
    total_count = Column(Integer)
    total_amount = Column(Numeric(15, 2))
    
    __table_args__ = (
        {"comment": "概念板块历史表"},
    )

