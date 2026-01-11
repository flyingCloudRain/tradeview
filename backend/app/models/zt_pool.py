"""
涨停池数据模型
"""
from sqlalchemy import Column, String, Date, Numeric, Integer, BigInteger, Time, Text
from datetime import date, time

from app.database.base import BaseModel


class ZtPool(BaseModel):
    """涨停池表"""
    __tablename__ = "zt_pool"
    
    date = Column(Date, nullable=False, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    change_percent = Column(Numeric(5, 2))  # 涨跌幅 (%)
    latest_price = Column(Numeric(10, 2))  # 最新价
    turnover_amount = Column(BigInteger)  # 成交额
    circulation_market_value = Column(Numeric(15, 2))  # 流通市值
    total_market_value = Column(Numeric(15, 2))  # 总市值
    turnover_rate = Column(Numeric(5, 2))  # 换手率 (%)
    limit_up_capital = Column(BigInteger)  # 封板资金
    first_limit_time = Column(Time)  # 首次封板时间
    last_limit_time = Column(Time)  # 最后封板时间
    explosion_count = Column(Integer, default=0)  # 炸板次数
    limit_up_statistics = Column(Text)  # 涨停统计
    consecutive_limit_count = Column(Integer)  # 连板数 (1 为首板)
    industry = Column(String(100), index=True)  # 所属行业
    concept = Column(Text)  # 概念
    limit_up_reason = Column(Text)  # 涨停原因
    
    __table_args__ = (
        {"comment": "涨停池表"},
    )


class ZtPoolDown(BaseModel):
    """跌停池表"""
    __tablename__ = "zt_pool_down"

    date = Column(Date, nullable=False, index=True)
    stock_code = Column(String(10), nullable=False, index=True)
    stock_name = Column(String(50), nullable=False)
    change_percent = Column(Numeric(5, 2))  # 涨跌幅 (%)
    latest_price = Column(Numeric(10, 2))  # 最新价
    turnover_amount = Column(BigInteger)  # 成交额
    circulation_market_value = Column(Numeric(15, 2))  # 流通市值
    total_market_value = Column(Numeric(15, 2))  # 总市值
    turnover_rate = Column(Numeric(5, 2))  # 换手率 (%)
    limit_up_capital = Column(BigInteger)  # 封板资金（跌停可为空）
    first_limit_time = Column(Time)  # 首次封板时间
    last_limit_time = Column(Time)  # 最后封板时间
    explosion_count = Column(Integer, default=0)  # 炸板次数
    limit_up_statistics = Column(Text)  # 涨停统计/跌停统计
    consecutive_limit_count = Column(Integer)  # 连板/连跌数
    industry = Column(String(100), index=True)  # 所属行业
    concept = Column(Text)  # 概念
    limit_up_reason = Column(Text)  # 跌停原因

    __table_args__ = (
        {"comment": "跌停池表"},
    )

