"""
AKShare工具函数
"""
import pandas as pd
import logging

logger = logging.getLogger(__name__)


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
        logger.error(f"AKShare调用失败: {func.__name__}, 错误: {str(e)}")
        return None

