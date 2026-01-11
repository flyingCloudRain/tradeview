"""
AKShare工具函数
"""
import akshare as ak
import pandas as pd
from typing import Optional
from datetime import date


def safe_akshare_call(func, *args, **kwargs):
    """
    安全调用AKShare函数，处理异常
    """
    try:
        result = func(*args, **kwargs)
        if result is None or (isinstance(result, pd.DataFrame) and result.empty):
            return None
        return result
    except Exception as e:
        print(f"AKShare调用失败: {func.__name__}, 错误: {str(e)}")
        return None

