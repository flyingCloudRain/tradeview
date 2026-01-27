"""
龙虎榜数据模型
"""
from sqlalchemy import Column, String, Date, Numeric, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import date

from app.database.base import BaseModel


class LhbDetail(BaseModel):
    """龙虎榜详情表"""
    __tablename__ = "lhb_detail"
    
    date = Column(Date, nullable=False, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    close_price = Column(Numeric(10, 2))
    change_percent = Column(Numeric(5, 2))
    net_buy_amount = Column(Numeric(15, 2))
    buy_amount = Column(Numeric(15, 2))
    sell_amount = Column(Numeric(15, 2))
    total_amount = Column(Numeric(15, 2))
    turnover_rate = Column(Numeric(5, 2))
    concept = Column(String(200), comment="概念板块")
    
    __table_args__ = (
        {"comment": "龙虎榜详情表"},
    )
    
    # 关系
    institutions = relationship("LhbInstitution", back_populates="lhb_detail", cascade="all, delete-orphan")


class LhbInstitution(BaseModel):
    """龙虎榜机构明细表"""
    __tablename__ = "lhb_institution"
    
    lhb_detail_id = Column(Integer, ForeignKey("lhb_detail.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    institution_name = Column(String(100))
    buy_amount = Column(Numeric(15, 2))
    sell_amount = Column(Numeric(15, 2))
    net_buy_amount = Column(Numeric(15, 2))
    flag = Column(String(10), comment="交易方向：买入/卖出", index=True)
    
    __table_args__ = (
        {"comment": "龙虎榜机构明细表"},
    )
    
    # 关系
    lhb_detail = relationship("LhbDetail", back_populates="institutions")


class LhbHotInstitution(BaseModel):
    """龙虎榜机构游资榜"""
    __tablename__ = "lhb_hot_institution"
    
    date = Column(Date, nullable=False, index=True, comment="上榜日期")
    institution_name = Column(String(200), nullable=False, index=True, comment="营业部名称")
    institution_code = Column(String(50), nullable=True, index=True, comment="营业部代码")
    buy_stock_count = Column(Integer, nullable=True, comment="买入个股数")
    sell_stock_count = Column(Integer, nullable=True, comment="卖出个股数")
    buy_amount = Column(Numeric(18, 2), nullable=True, comment="买入总金额")
    sell_amount = Column(Numeric(18, 2), nullable=True, comment="卖出总金额")
    net_amount = Column(Numeric(18, 2), nullable=True, comment="总买卖净额")
    buy_stocks = Column(Text, nullable=True, comment="买入股票列表")
    
    __table_args__ = (
        {"comment": "龙虎榜机构游资榜（营业部榜）"},
    )


class ActiveBranch(BaseModel):
    """活跃营业部表（从 stock_lhb_hyyyb_em 获取）"""
    __tablename__ = "active_branch"
    
    date = Column(Date, nullable=False, index=True, comment="上榜日期")
    institution_name = Column(String(200), nullable=False, index=True, comment="营业部名称")
    institution_code = Column(String(50), nullable=True, index=True, comment="营业部代码")
    buy_stock_count = Column(Integer, nullable=True, comment="买入个股数")
    sell_stock_count = Column(Integer, nullable=True, comment="卖出个股数")
    buy_amount = Column(Numeric(18, 2), nullable=True, comment="买入总金额")
    sell_amount = Column(Numeric(18, 2), nullable=True, comment="卖出总金额")
    net_amount = Column(Numeric(18, 2), nullable=True, comment="总买卖净额")
    buy_stocks = Column(Text, nullable=True, comment="买入股票列表")
    
    __table_args__ = (
        UniqueConstraint("date", "institution_code", name="uq_active_branch"),
        {"comment": "活跃营业部表"},
    )

