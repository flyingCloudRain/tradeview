"""
股票概念板块数据模型
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import BaseModel


class StockConcept(BaseModel):
    """股票概念板块表"""
    __tablename__ = "stock_concept"
    
    name = Column(String(100), nullable=False, unique=True, comment="概念板块名称")
    code = Column(String(20), unique=True, nullable=True, comment="概念板块代码")
    description = Column(Text, nullable=True, comment="概念板块描述")
    
    # 关联关系
    stock_mappings = relationship(
        "StockConceptMapping",
        back_populates="concept",
        cascade="all, delete-orphan"
    )
    
    trading_calendar_mappings = relationship(
        "TradingCalendarConcept",
        back_populates="concept",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        {"comment": "股票概念板块表"},
    )


class StockConceptMapping(BaseModel):
    """股票概念板块通用关联表"""
    __tablename__ = "stock_concept_mapping"
    
    stock_name = Column(String(50), nullable=False, index=True, comment="股票名称")
    concept_id = Column(Integer, ForeignKey('stock_concept.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 关联关系
    concept = relationship("StockConcept", back_populates="stock_mappings")
    
    __table_args__ = (
        {"comment": "股票概念板块通用关联表"},
    )
    
    # 添加唯一约束（通过迁移文件创建，这里仅作说明）


class TradingCalendarConcept(BaseModel):
    """交易日历概念板块关联表"""
    __tablename__ = "trading_calendar_concept"
    
    trading_calendar_id = Column(Integer, ForeignKey('trading_calendar.id', ondelete='CASCADE'), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey('stock_concept.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 关联关系
    concept = relationship("StockConcept", back_populates="trading_calendar_mappings")
    
    __table_args__ = (
        {"comment": "交易日历概念板块关联表（可选，用于覆盖或补充）"},
    )
