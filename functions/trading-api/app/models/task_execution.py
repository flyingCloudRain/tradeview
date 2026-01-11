"""
任务执行历史数据模型
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Enum as SQLEnum, TypeDecorator
from datetime import datetime
import enum

from app.database.base import BaseModel


class TaskStatus(str, enum.Enum):
    """任务状态"""
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 执行中
    SUCCESS = "success"  # 成功
    FAILED = "failed"    # 失败


def _default_task_status():
    """默认任务状态"""
    return TaskStatus.PENDING


class TaskStatusEnum(TypeDecorator):
    """确保枚举值被正确使用的类型装饰器"""
    impl = String
    cache_ok = True
    
    def __init__(self):
        super().__init__(length=20)
    
    def process_bind_param(self, value, dialect):
        """绑定参数时，确保使用枚举值而不是名称"""
        if value is None:
            return None
        if isinstance(value, TaskStatus):
            return value.value
        if isinstance(value, str):
            # 如果传入的是字符串，验证是否为有效值
            valid_values = [s.value for s in TaskStatus]
            if value.lower() in valid_values:
                return value.lower()
            raise ValueError(f"Invalid TaskStatus value: {value}. Valid values: {valid_values}")
        return value
    
    def process_result_value(self, value, dialect):
        """从数据库读取时，转换为枚举"""
        if value is None:
            return None
        if isinstance(value, TaskStatus):
            return value
        # 从数据库读取的是字符串值，转换为枚举
        for status in TaskStatus:
            if status.value == value:
                return status
        return value


class TaskExecution(BaseModel):
    """任务执行历史表"""
    __tablename__ = "task_execution"
    
    task_name = Column(String(100), nullable=False, index=True, comment="任务名称")
    task_type = Column(String(50), nullable=False, index=True, comment="任务类型")
    status = Column(TaskStatusEnum(), nullable=False, default=_default_task_status, index=True, comment="执行状态")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    duration = Column(String(20), nullable=True, comment="执行时长（秒）")
    result = Column(JSON, nullable=True, comment="执行结果详情")
    error_message = Column(Text, nullable=True, comment="错误信息")
    triggered_by = Column(String(20), nullable=False, default="scheduler", comment="触发方式：scheduler/manual")
    target_date = Column(String(20), nullable=True, comment="目标日期")
    
    __table_args__ = (
        {"comment": "任务执行历史表"},
    )

