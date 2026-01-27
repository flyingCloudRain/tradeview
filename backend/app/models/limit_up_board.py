"""
涨停板分析数据模型
"""
from sqlalchemy import Column, String, Date, Text, Integer, Index, JSON, Numeric, Time, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date, time

from app.database.base import BaseModel


class LimitUpBoard(BaseModel):
    """涨停板分析表"""
    __tablename__ = "limit_up_board"
    
    date = Column(Date, nullable=False, index=True, comment="日期")
    board_name = Column(String(100), nullable=False, index=True, comment="板块名称")
    board_stock_count = Column(Integer, nullable=True, comment="板块股票数量")
    stock_code = Column(String(20), nullable=False, index=True, comment="股票代码")
    stock_name = Column(String(50), nullable=False, index=True, comment="股票名称")
    limit_up_days = Column(String(20), nullable=True, comment="涨停天数（如：11 天 9 板）")
    limit_up_time = Column(Time, nullable=True, comment="涨停时间")
    circulation_market_value = Column(Numeric(15, 2), nullable=True, comment="流通市值（亿元）")
    turnover_amount = Column(Numeric(15, 2), nullable=True, comment="成交额（亿元）")
    keywords = Column(Text, nullable=True, comment="涨停关键词（原始文本）")
    limit_up_reason = Column(Text, nullable=True, comment="涨停原因（解析后的主要原因）")
    tags = Column(JSON, nullable=True, comment="涨停标签列表（从关键字解析）")
    
    # 新增字段
    price_change_pct = Column(Numeric(10, 2), nullable=True, comment="涨跌幅（%）")
    latest_price = Column(Numeric(10, 2), nullable=True, comment="最新价")
    turnover = Column(Numeric(20, 0), nullable=True, comment="成交额")
    total_market_value = Column(Numeric(15, 2), nullable=True, comment="总市值（亿元）")
    turnover_rate = Column(Numeric(10, 2), nullable=True, comment="换手率（%）")
    sealing_capital = Column(Numeric(20, 0), nullable=True, comment="封板资金")
    first_sealing_time = Column(Time, nullable=True, comment="首次封板时间（格式：09:25:00）")
    last_sealing_time = Column(Time, nullable=True, comment="最后封板时间（格式：09:25:00）")
    board_breaking_count = Column(Integer, nullable=True, comment="炸板次数")
    limit_up_statistics = Column(String(100), nullable=True, comment="涨停统计")
    consecutive_board_count = Column(Integer, nullable=True, comment="连板数（1为首板）")
    industry = Column(String(100), nullable=True, index=True, comment="所属行业")
    
    # 关联关系
    concept_mappings = relationship(
        "LimitUpBoardConcept",
        back_populates="limit_up_board",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_date_board', 'date', 'board_name'),
        Index('idx_date_stock', 'date', 'stock_code'),
        {"comment": "涨停板分析表"},
    )


class LimitUpBoardConcept(BaseModel):
    """涨停板分析概念板块关联表"""
    __tablename__ = "limit_up_board_concept"
    
    limit_up_board_id = Column(Integer, ForeignKey('limit_up_board.id', ondelete='CASCADE'), nullable=False, index=True)
    concept_id = Column(Integer, ForeignKey('stock_concept.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 关联关系
    limit_up_board = relationship("LimitUpBoard", back_populates="concept_mappings")
    concept = relationship("StockConcept")
    
    __table_args__ = (
        Index('idx_limit_up_board_concept', 'limit_up_board_id', 'concept_id', unique=True),
        {"comment": "涨停板分析概念板块关联表"},
    )
