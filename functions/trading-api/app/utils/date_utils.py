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

