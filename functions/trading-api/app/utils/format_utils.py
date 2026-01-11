"""
格式化工具函数
"""
from decimal import Decimal
from typing import Optional, Union


def format_amount(amount: Optional[Union[int, float, Decimal]]) -> str:
    """格式化金额"""
    if amount is None:
        return "-"
    
    amount = float(amount)
    if amount >= 100000000:
        return f"{amount / 100000000:.2f}亿"
    elif amount >= 10000:
        return f"{amount / 10000:.2f}万"
    else:
        return f"{amount:.2f}"


def format_percent(value: Optional[Union[int, float, Decimal]], decimals: int = 2) -> str:
    """格式化百分比"""
    if value is None:
        return "-"
    
    value = float(value)
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_price(price: Optional[Union[int, float, Decimal]], decimals: int = 2) -> str:
    """格式化价格"""
    if price is None:
        return "-"
    return f"{float(price):.{decimals}f}"


def safe_float(value: Optional[Union[str, int, float]]) -> Optional[float]:
    """安全转换为float"""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value: Optional[Union[str, int, float]]) -> Optional[int]:
    """安全转换为int"""
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None

