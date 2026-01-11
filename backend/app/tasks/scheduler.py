"""
定时任务调度器
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from datetime import date, datetime
from typing import Union
import time

from app.database.session import SessionLocal
from app.utils.date_utils import get_trading_date
from app.utils.sync_result import SyncResult
from app.models.task_execution import TaskStatus


def init_scheduler():
    """初始化调度器"""
    # 使用北京时间
    beijing_tz = timezone("Asia/Shanghai")
    scheduler = BackgroundScheduler(timezone=beijing_tz)
    
    # 每日收盘后执行数据同步（北京时间 16:00）
    scheduler.add_job(
        sync_daily_data,
        trigger=CronTrigger(hour=16, minute=0, timezone=beijing_tz),
        id='sync_daily_data',
        name='每日数据同步',
        replace_existing=True
    )
    
    return scheduler


def sync_daily_data(task_types: list[str] | None = None, target_date: date | None = None, execution_id: int | None = None):
    """
    同步每日数据
    调用各个服务的数据同步方法
    
    Args:
        task_types: 要执行的任务类型列表，None表示执行所有任务
        target_date: 目标日期，None表示使用交易日
        execution_id: 已存在的执行记录ID，如果提供则使用现有记录，否则创建新记录
    """
    db = SessionLocal()
    execution = None
    try:
        if target_date is None:
            target_date = get_trading_date()
        if target_date is None:
            raise ValueError("无法获取交易日，请指定target_date")
        target_date_str = target_date.strftime("%Y-%m-%d")
        print(f"开始同步 {target_date} 的数据...")
        
        # 延迟导入避免循环导入
        from app.services.task_service import TaskService
        
        # 如果提供了execution_id，使用现有记录；否则创建新记录
        if execution_id:
            execution = TaskService.get_task_execution_by_id(db=db, execution_id=execution_id)
            if not execution:
                raise ValueError(f"执行记录不存在: {execution_id}")
            execution.status = TaskStatus.RUNNING
            db.commit()
        else:
            # 创建总体执行记录
            task_name = "每日数据同步" if not task_types else f"数据同步任务 ({', '.join(task_types)})"
            execution = TaskService.create_execution_record(
                db=db,
                task_name=task_name,
                task_type=",".join(task_types) if task_types else "all",
                triggered_by="scheduler",
                target_date=target_date_str,
            )
            execution.status = TaskStatus.RUNNING
            db.commit()
        
        execution_id = execution.id
        
        from app.services.lhb_service import LhbService
        from app.services.zt_pool_service import ZtPoolService
        from app.services.zt_pool_service import ZtPoolDownService
        from app.services.index_service import IndexService
        from app.services.fund_flow_service import FundFlowService
        from app.services.capital_service import CapitalService
        
        task_map = {
            "lhb": lambda: LhbService.sync_data(db, target_date),
            "zt_pool": lambda: ZtPoolService.sync_data(db, target_date),
            "zt_pool_down": lambda: ZtPoolDownService.sync_data(db, target_date),
            "index": lambda: IndexService.sync_data(db, target_date),
            "stock_fund_flow": lambda: FundFlowService.sync_data(db, target_date),
            "fund_flow_concept": lambda: FundFlowService.sync_concept_fund_flow(db, target_date, limit=200),
            "capital": lambda: CapitalService.sync_data(db, target_date),
        }

        selected_keys = task_types if task_types else list(task_map.keys())
        results = {}
        error_details = {}
        task_results = {}

        for key in selected_keys:
            task_fn = task_map.get(key)
            if not task_fn:
                print(f"跳过未知任务: {key}")
                error_details[key] = "未知任务类型"
                continue
            
            task_start_time = time.time()
            try:
                result = task_fn()
                # 兼容旧代码：如果返回 bool，转换为 SyncResult
                if isinstance(result, bool):
                    if result:
                        result = SyncResult.success_result(f"{key} 同步成功")
                    else:
                        result = SyncResult.failure_result(f"{key} 同步失败", "返回 False")
                
                results[key] = result
                task_duration = time.time() - task_start_time
                task_results[key] = {
                    "success": result.success if isinstance(result, SyncResult) else result,
                    "duration": f"{task_duration:.2f}",
                    "message": str(result) if isinstance(result, SyncResult) else ("成功" if result else "失败"),
                }
                
                # 打印详细结果
                if result.success if isinstance(result, SyncResult) else result:
                    print(f"✅ {key}: {result}")
                else:
                    print(f"❌ {key}: {result}")
                    error_details[key] = result.error if isinstance(result, SyncResult) else "未知错误"
                    
            except Exception as e:
                error_msg = f"{key} 执行异常: {str(e)}"
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()
                results[key] = SyncResult.failure_result(str(e), error_msg)
                error_details[key] = str(e)
                task_duration = time.time() - task_start_time
                task_results[key] = {
                    "success": False,
                    "duration": f"{task_duration:.2f}",
                    "message": error_msg,
                }

        success_count = sum(1 for v in results.values() if (isinstance(v, SyncResult) and v.success) or (isinstance(v, bool) and v))
        total_count = len(results)
        
        print(f"\n{'='*60}")
        print(f"完成同步 {target_date} 的数据")
        print(f"成功: {success_count}/{total_count}")
        print(f"{'='*60}")
        
        if error_details:
            print(f"\n失败任务详情:")
            for task_name, error in error_details.items():
                print(f"  - {task_name}: {error}")
        
        print(f"\n详细结果:")
        for key, result in results.items():
            if isinstance(result, SyncResult):
                status = "✅" if result.success else "❌"
                print(f"  {status} {key}: {result}")
            else:
                status = "✅" if result else "❌"
                print(f"  {status} {key}: {'成功' if result else '失败'}")
        
        # 更新执行记录状态（延迟导入避免循环导入）
        if execution_id:
            from app.services.task_service import TaskService, make_json_serializable
            overall_duration = time.time() - execution.start_time.timestamp() if execution.start_time else 0
            
            # 确保result字典中的所有值都是JSON可序列化的
            serializable_result = make_json_serializable({
                "success_count": success_count,
                "total_count": total_count,
                "task_results": task_results,
            })
            
            TaskService.update_execution_status(
                db=db,
                execution_id=execution_id,
                status=TaskStatus.SUCCESS if success_count == total_count else TaskStatus.FAILED,
                result=serializable_result,
                error_message="\n".join([f"{k}: {v}" for k, v in error_details.items()]) if error_details else None,
            )
    except Exception as e:
        print(f"数据同步失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 更新执行记录状态为失败（延迟导入避免循环导入）
        if execution_id:
            try:
                from app.services.task_service import TaskService
                TaskService.update_execution_status(
                    db=db,
                    execution_id=execution_id,
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                )
            except:
                pass
    finally:
        db.close()

