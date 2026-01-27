"""
股票概念板块数据模型（支持2-3级层级）
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from typing import List

from app.database.base import BaseModel


class StockConcept(BaseModel):
    """股票概念板块表（支持2-3级层级）"""
    __tablename__ = "stock_concept"
    
    name = Column(String(100), nullable=False, comment="概念板块名称")
    code = Column(String(20), unique=True, nullable=True, comment="概念板块代码")
    description = Column(Text, nullable=True, comment="概念板块描述")
    
    # 层级相关字段
    parent_id = Column(Integer, ForeignKey('stock_concept.id', ondelete='SET NULL'), 
                       nullable=True, comment="父概念ID，NULL表示一级概念")
    level = Column(Integer, nullable=False, default=1, comment="层级：1=一级，2=二级，3=三级")
    path = Column(String(500), nullable=True, comment="层级路径，如：1/5/12")
    sort_order = Column(Integer, default=0, comment="同级排序顺序")
    stock_count = Column(Integer, default=0, comment="关联的个股数量（冗余字段）")
    
    # 关联关系
    parent = relationship(
        "StockConcept",
        remote_side="StockConcept.id",
        backref="children"
    )
    
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
        CheckConstraint('level IN (1, 2, 3)', name='check_level_range'),
        CheckConstraint(
            '(parent_id IS NULL AND level = 1) OR (parent_id IS NOT NULL AND level > 1)',
            name='check_level_parent'
        ),
        {"comment": "股票概念板块表（支持2-3级层级）"},
    )
    
    def get_full_path(self) -> List[int]:
        """获取完整层级路径"""
        if self.path:
            return [int(x) for x in self.path.split('/') if x]
        return []
    
    def get_all_ancestors(self) -> List['StockConcept']:
        """获取所有祖先概念"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_all_descendants(self) -> List['StockConcept']:
        """获取所有后代概念（递归）"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants


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
