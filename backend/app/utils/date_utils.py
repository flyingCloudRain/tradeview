"""
日期工具函数
"""
from datetime import date, datetime
from typing import Optional


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def format_date(d: Optional[date]) -> Optional[str]:
    """格式化日期为字符串"""
    if not d:
        return None
    return d.strftime("%Y-%m-%d")


def get_today() -> date:
    """获取今天日期"""
    return date.today()


def get_trading_date() -> date:
    """
    获取交易日（如果是周末，返回最近的交易日）
    简化版本，实际应该考虑节假日
    """
    today = date.today()
    # 如果是周六，返回周五
    if today.weekday() == 5:
        from datetime import timedelta
        return today - timedelta(days=1)
    # 如果是周日，返回周五
    elif today.weekday() == 6:
        from datetime import timedelta
        return today - timedelta(days=2)
    return today


def get_trading_dates_before(db, end_date: date, count: int) -> list[date]:
    """
    获取从end_date往前推count个交易日
    
    Args:
        db: 数据库会话
        end_date: 结束日期
        count: 需要获取的交易日数量
        
    Returns:
        list[date]: 交易日列表（从新到旧）
    """
    from datetime import timedelta
    from app.models.fund_flow import StockFundFlow
    
    # 方法1：从资金流数据中获取有数据的日期（更准确）
    start_date = end_date - timedelta(days=count * 2 + 10)
    
    trading_dates_query = db.query(StockFundFlow.date).filter(
        StockFundFlow.date <= end_date,
        StockFundFlow.date >= start_date
    ).distinct().order_by(StockFundFlow.date.desc()).limit(count).all()
    
    trading_dates = [row[0] for row in trading_dates_query]
    
    # 如果数据库中没有足够的交易日，使用简化方法（排除周末）
    if len(trading_dates) < count:
        trading_dates = []
        current_date = end_date
        days_checked = 0
        while len(trading_dates) < count and days_checked < count * 2 + 10:
            # 排除周末（周六=5, 周日=6）
            if current_date.weekday() < 5:
                trading_dates.append(current_date)
            current_date -= timedelta(days=1)
            days_checked += 1
    
    return trading_dates[:count]

