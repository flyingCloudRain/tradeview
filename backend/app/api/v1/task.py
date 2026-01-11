"""
任务管理API路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.database.session import get_db
from app.services.task_service import TaskService
from app.schemas.task import (
    TaskExecutionListResponse,
    TaskExecutionResponse,
    TaskRunRequest,
    TaskRunResponse,
)
from app.models.task_execution import TaskStatus

router = APIRouter()


@router.get("/executions", response_model=TaskExecutionListResponse)
def get_task_executions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_type: Optional[str] = Query(None, description="任务类型"),
    status: Optional[str] = Query(None, description="执行状态"),
    task_name: Optional[str] = Query(None, description="任务名称"),
    db: Session = Depends(get_db),
):
    """获取任务执行历史列表"""
    task_status = None
    if status:
        try:
            task_status = TaskStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态值: {status}")
    
    result = TaskService.get_task_executions(
        db=db,
        page=page,
        page_size=page_size,
        task_type=task_type,
        status=task_status,
        task_name=task_name,
    )
    
    return result


@router.get("/executions/{execution_id}", response_model=TaskExecutionResponse)
def get_task_execution(
    execution_id: int,
    db: Session = Depends(get_db),
):
    """获取任务执行详情"""
    execution = TaskService.get_task_execution_by_id(db=db, execution_id=execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="任务执行记录不存在")
    return execution


@router.get("/status", response_model=dict)
def get_task_status_summary(db: Session = Depends(get_db)):
    """获取任务状态汇总"""
    return TaskService.get_task_status_summary(db=db)


@router.post("/run", response_model=TaskRunResponse)
def run_tasks(
    request: TaskRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """手动执行任务（异步）"""
    try:
        # 创建任务执行记录
        execution = TaskService.create_task_execution(
            db=db,
            task_types=request.task_types,
            target_date=request.target_date,
        )
        
        # 将任务添加到后台任务队列
        background_tasks.add_task(
            TaskService.execute_task_async,
            execution_id=execution.id,
            task_types=request.task_types,
            target_date=request.target_date,
        )
        
        return TaskRunResponse(
            execution_id=execution.id,
            message="任务已提交，正在后台执行",
            task_types=request.task_types or [],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")


@router.get("/task-types", response_model=dict)
def get_task_types():
    """获取所有任务类型"""
    return {
        "task_types": list(TaskService.TASK_NAMES.keys()),
        "task_names": TaskService.TASK_NAMES,
    }

