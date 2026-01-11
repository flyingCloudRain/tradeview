"""
同步任务结果工具类
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SyncResult:
    """同步任务结果"""
    success: bool
    message: str = ""
    error: Optional[str] = None
    count: int = 0
    
    def __bool__(self):
        """支持 bool() 转换，保持向后兼容"""
        return self.success
    
    @classmethod
    def success_result(cls, message: str = "", count: int = 0) -> "SyncResult":
        """创建成功结果"""
        return cls(success=True, message=message, count=count)
    
    @classmethod
    def failure_result(cls, error: str, message: str = "") -> "SyncResult":
        """创建失败结果"""
        return cls(success=False, error=error, message=message)
    
    def __str__(self):
        if self.success:
            return f"成功: {self.message}" + (f" (共 {self.count} 条)" if self.count > 0 else "")
        else:
            return f"失败: {self.error}" + (f" ({self.message})" if self.message else "")

