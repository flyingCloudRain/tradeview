"""
任务管理服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date as date_type
import time

from app.models.task_execution import TaskExecution, TaskStatus
from app.tasks.scheduler import sync_daily_data
from app.utils.date_utils import get_trading_date
from app.utils.sync_result import SyncResult


def make_json_serializable(obj: Any) -> Any:
    """递归转换对象为JSON可序列化格式"""
    if isinstance(obj, (date_type, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__') and not isinstance(obj, (str, int, float, bool, type(None))):
        return make_json_serializable(obj.__dict__)
    else:
        return obj


class TaskService:
    """任务管理服务"""
    
    TASK_NAMES = {
        "lhb": "龙虎榜数据同步",
        "lhb_institution": "龙虎榜机构数据同步",
        "zt_pool": "涨停池数据同步",
        "zt_pool_down": "跌停池数据同步",
        "index": "大盘指数数据同步",
        "stock_fund_flow": "个股资金流数据同步",
        "fund_flow_concept": "概念资金流数据同步",
        "capital": "活跃机构数据同步",
    }
    
    @staticmethod
    def get_task_executions(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        task_type: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        task_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取任务执行历史列表（优化版本）"""
        try:
            # 构建基础查询
            query = db.query(TaskExecution)
            
            if task_type:
                query = query.filter(TaskExecution.task_type == task_type)
            if status:
                query = query.filter(TaskExecution.status == status)
            if task_name:
                query = query.filter(TaskExecution.task_name == task_name)
            
            # 优化：先获取分页数据，再获取总数（如果数据量大，可以只估算）
            # 先排序并分页查询
            items_query = query.order_by(desc(TaskExecution.start_time))
            items = items_query.offset((page - 1) * page_size).limit(page_size).all()
            
            # 获取总数（如果第一页没有数据，可能不需要总数）
            if page == 1 and len(items) < page_size:
                # 如果第一页数据不足一页，总数就是当前数据量
                total = len(items)
            else:
                # 否则需要计算总数
                total = query.count()
            
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        except Exception as e:
            print(f"[TaskService] 获取任务执行历史失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 返回空结果，避免前端完全无响应
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
            }
    
    @staticmethod
    def get_task_execution_by_id(db: Session, execution_id: int) -> Optional[TaskExecution]:
        """根据ID获取任务执行记录"""
        return db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
    
    @staticmethod
    def get_latest_executions(db: Session, limit: int = 10) -> List[TaskExecution]:
        """获取最新的任务执行记录"""
        return db.query(TaskExecution).order_by(desc(TaskExecution.start_time)).limit(limit).all()
    
    @staticmethod
    def get_task_status_summary(db: Session) -> Dict[str, Any]:
        """获取任务状态汇总（优化版本，使用更高效的查询）"""
        try:
            # 优化：使用窗口函数或更简单的查询方式
            # 首先获取每个任务类型的最新执行记录ID
            from sqlalchemy import distinct
            
            # 方法1：使用窗口函数（如果数据库支持）或子查询
            # 为了兼容性，使用更简单的方法：先获取每个任务类型的最新时间，然后查询
            
            # 获取每个任务类型的最新执行时间（单次查询）
            latest_times = db.query(
                TaskExecution.task_type,
                func.max(TaskExecution.start_time).label('max_time')
            ).group_by(TaskExecution.task_type).all()
            
            if not latest_times:
                # 如果没有执行记录，返回所有任务类型的默认状态
                return {
                    task_type: {
                        "task_name": task_name,
                        "status": "pending",
                        "last_run_time": None,
                        "last_success_time": None,
                        "duration": None,
                        "error_message": None,
                    }
                    for task_type, task_name in TaskService.TASK_NAMES.items()
                }
            
            # 构建查询条件：获取每个任务类型的最新记录
            conditions = []
            for task_type, max_time in latest_times:
                conditions.append(
                    (TaskExecution.task_type == task_type) & 
                    (TaskExecution.start_time == max_time)
                )
            
            # 使用 OR 条件一次性查询所有最新记录
            from sqlalchemy import or_
            latest_executions = db.query(TaskExecution).filter(
                or_(*conditions)
            ).all()
            
            # 获取每个任务类型最后一次成功执行的时间（单次查询）
            success_times = db.query(
                TaskExecution.task_type,
                func.max(TaskExecution.start_time).label('max_success_time')
            ).filter(TaskExecution.status == TaskStatus.SUCCESS).group_by(TaskExecution.task_type).all()
            
            # 创建成功执行时间的映射
            success_time_map = {task_type: max_time for task_type, max_time in success_times}
            
            # 创建执行记录的映射
            execution_map = {}
            for execution in latest_executions:
                success_time = success_time_map.get(execution.task_type)
                execution_map[execution.task_type] = {
                    "task_name": execution.task_name,
                    "status": execution.status.value,
                    "last_run_time": execution.start_time.isoformat() if execution.start_time else None,
                    "last_success_time": success_time.isoformat() if success_time else None,
                    "duration": execution.duration,
                    "error_message": execution.error_message,
                }
            
            # 确保所有任务类型都有状态记录
            summary = {}
            for task_type, task_name in TaskService.TASK_NAMES.items():
                if task_type in execution_map:
                    summary[task_type] = execution_map[task_type]
                else:
                    # 没有执行记录的任务，检查是否有成功记录
                    last_success_time = success_time_map.get(task_type)
                    summary[task_type] = {
                        "task_name": task_name,
                        "status": "pending",
                        "last_run_time": None,
                        "last_success_time": last_success_time.isoformat() if last_success_time else None,
                        "duration": None,
                        "error_message": None,
                    }
            
            return summary
            
        except Exception as e:
            # 如果查询失败，返回错误信息但不会导致整个服务崩溃
            print(f"[TaskService] 获取任务状态汇总失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 返回默认状态，避免前端完全无响应
            return {
                task_type: {
                    "task_name": task_name,
                    "status": "error",
                    "last_run_time": None,
                    "last_success_time": None,
                    "duration": None,
                    "error_message": f"查询失败: {str(e)}",
                }
                for task_type, task_name in TaskService.TASK_NAMES.items()
            }
    
    @staticmethod
    def create_execution_record(
        db: Session,
        task_name: str,
        task_type: str,
        triggered_by: str = "manual",
        target_date: Optional[str] = None,
    ) -> TaskExecution:
        """创建任务执行记录"""
        execution = TaskExecution(
            task_name=task_name,
            task_type=task_type,
            status=TaskStatus.PENDING,
            start_time=datetime.now(),
            triggered_by=triggered_by,
            target_date=target_date,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        return execution
    
    @staticmethod
    def update_execution_status(
        db: Session,
        execution_id: int,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> Optional[TaskExecution]:
        """更新任务执行状态"""
        execution = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
        if not execution:
            return None
        
        execution.status = status
        execution.end_time = datetime.now()
        
        # 计算执行时长
        if execution.start_time:
            duration_seconds = (execution.end_time - execution.start_time).total_seconds()
            execution.duration = f"{duration_seconds:.2f}"
        
        if result:
            # 确保result中的所有值都是JSON可序列化的
            execution.result = make_json_serializable(result)
        if error_message:
            execution.error_message = error_message
        
        db.commit()
        db.refresh(execution)
        return execution
    
    @staticmethod
    def create_task_execution(
        db: Session,
        task_types: Optional[List[str]] = None,
        target_date: Optional[str] = None,
    ) -> TaskExecution:
        """创建任务执行记录（用于异步执行）"""
        from datetime import datetime as dt
        
        # 确定目标日期
        target_date_obj = None
        if target_date:
            try:
                target_date_obj = dt.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"日期格式错误: {target_date}，请使用 YYYY-MM-DD 格式")
        else:
            target_date_obj = get_trading_date()
            if not target_date_obj:
                raise ValueError("无法获取交易日，请指定target_date")
            target_date = target_date_obj.strftime("%Y-%m-%d")
        
        # 创建执行记录
        task_name = "数据同步任务" if not task_types else f"数据同步任务 ({', '.join(task_types)})"
        execution = TaskService.create_execution_record(
            db=db,
            task_name=task_name,
            task_type=",".join(task_types) if task_types else "all",
            triggered_by="manual",
            target_date=target_date,
        )
        
        # 更新状态为运行中
        execution.status = TaskStatus.RUNNING
        db.commit()
        db.refresh(execution)
        
        return execution
    
    @staticmethod
    def execute_task_async(
        execution_id: int,
        task_types: Optional[List[str]] = None,
        target_date: Optional[str] = None,
    ):
        """异步执行任务"""
        from datetime import datetime as dt
        
        try:
            # 确定目标日期
            target_date_obj = None
            if target_date:
                try:
                    target_date_obj = dt.strptime(target_date, "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError(f"日期格式错误: {target_date}，请使用 YYYY-MM-DD 格式")
            else:
                target_date_obj = get_trading_date()
                if not target_date_obj:
                    raise ValueError("无法获取交易日，请指定target_date")
            
            # 执行任务（传入execution_id使用现有记录）
            print(f"开始异步执行任务 {execution_id}...")
            sync_daily_data(task_types=task_types, target_date=target_date_obj, execution_id=execution_id)
            print(f"任务 {execution_id} 执行完成")
            
        except Exception as e:
            print(f"任务 {execution_id} 执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 更新状态为失败（sync_daily_data内部会处理，但这里也处理以防万一）
            from app.database.session import SessionLocal
            db = SessionLocal()
            try:
                TaskService.update_execution_status(
                    db=db,
                    execution_id=execution_id,
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                )
            except Exception as update_error:
                print(f"更新任务状态失败: {str(update_error)}")
            finally:
                db.close()
    
    @staticmethod
    def run_tasks(
        db: Session,
        task_types: Optional[List[str]] = None,
        target_date: Optional[str] = None,
    ) -> TaskExecution:
        """手动执行任务（同步方式，保留用于向后兼容）"""
        from datetime import datetime as dt
        
        # 确定目标日期
        target_date_obj = None
        if target_date:
            try:
                target_date_obj = dt.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f"日期格式错误: {target_date}，请使用 YYYY-MM-DD 格式")
        else:
            target_date_obj = get_trading_date()
            if not target_date_obj:
                raise ValueError("无法获取交易日，请指定target_date")
            target_date = target_date_obj.strftime("%Y-%m-%d")
        
        # 创建执行记录
        task_name = "数据同步任务" if not task_types else f"数据同步任务 ({', '.join(task_types)})"
        execution = TaskService.create_execution_record(
            db=db,
            task_name=task_name,
            task_type=",".join(task_types) if task_types else "all",
            triggered_by="manual",
            target_date=target_date,
        )
        
        # 更新状态为运行中
        execution.status = TaskStatus.RUNNING
        db.commit()
        
        try:
            # 执行任务
            start_time = time.time()
            sync_daily_data(task_types=task_types, target_date=target_date_obj)
            end_time = time.time()
            duration = end_time - start_time
            
            # 更新状态为成功
            TaskService.update_execution_status(
                db=db,
                execution_id=execution.id,
                status=TaskStatus.SUCCESS,
                result={"duration": f"{duration:.2f}", "task_types": task_types or "all"},
            )
        except Exception as e:
            # 更新状态为失败
            TaskService.update_execution_status(
                db=db,
                execution_id=execution.id,
                status=TaskStatus.FAILED,
                error_message=str(e),
            )
            raise
        
        return execution

