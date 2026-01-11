"""
任务执行Pydantic模式
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.task_execution import TaskStatus


class TaskExecutionBase(BaseModel):
    """任务执行基础模式"""
    task_name: str = Field(..., description="任务名称")
    task_type: str = Field(..., description="任务类型")
    status: TaskStatus = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration: Optional[str] = Field(None, description="执行时长")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果详情")
    error_message: Optional[str] = Field(None, description="错误信息")
    triggered_by: str = Field(..., description="触发方式")
    target_date: Optional[str] = Field(None, description="目标日期")


class TaskExecutionResponse(TaskExecutionBase):
    """任务执行响应"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaskExecutionListResponse(BaseModel):
    """任务执行列表响应"""
    items: List[TaskExecutionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskExecutionCreate(BaseModel):
    """创建任务执行记录"""
    task_name: str
    task_type: str
    triggered_by: str = "manual"
    target_date: Optional[str] = None


class TaskRunRequest(BaseModel):
    """手动执行任务请求"""
    task_types: Optional[List[str]] = Field(None, description="任务类型列表，不指定则执行所有任务")
    target_date: Optional[str] = Field(None, description="目标日期，格式：YYYY-MM-DD，不指定则使用交易日")


class TaskRunResponse(BaseModel):
    """任务执行响应"""
    execution_id: int
    message: str
    task_types: List[str]

