"""
定时任务调度器（性能优化版本）
使用线程池执行器隔离任务执行，避免影响API响应时间
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from datetime import date, datetime
from typing import Union, Optional
import time
import threading
from concurrent.futures import ThreadPoolExecutor as ConcurrentThreadPoolExecutor, TimeoutError as FutureTimeoutError, as_completed
import logging

# 配置日志
logger = logging.getLogger(__name__)

from app.database.session import SessionLocal
from app.utils.date_utils import get_trading_date
from app.utils.sync_result import SyncResult
from app.models.task_execution import TaskStatus

# 任务执行器配置
# 使用独立的线程池执行定时任务，避免阻塞主线程和API请求
# APScheduler 的 ThreadPoolExecutor 不支持 thread_name_prefix 参数
TASK_EXECUTOR = ThreadPoolExecutor(max_workers=3)
# 任务执行超时时间（秒），防止任务执行时间过长
TASK_TIMEOUT = 3600  # 1小时超时


def _execute_task_with_timeout(task_func, timeout: int = TASK_TIMEOUT):
    """
    在独立线程中执行任务，带超时控制
    
    Args:
        task_func: 要执行的任务函数
        timeout: 超时时间（秒）
    
    Returns:
        任务执行结果
    """
    def run_task():
        try:
            return task_func()
        except Exception as e:
            return SyncResult.failure_result(str(e), f"任务执行异常: {str(e)}")
    
    with ConcurrentThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_task)
        try:
            result = future.result(timeout=timeout)
            return result
        except FutureTimeoutError:
            return SyncResult.failure_result("任务执行超时", f"任务执行超过 {timeout} 秒")
        except Exception as e:
            return SyncResult.failure_result(str(e), f"任务执行异常: {str(e)}")


def sync_lhb_institution_data(target_date: date | None = None):
    """
    同步龙虎榜个股对应的交易机构数据
    此任务应在龙虎榜基础数据同步之后执行
    
    Args:
        target_date: 目标日期，None表示使用交易日
    """
    # 使用独立的数据库连接，避免与API请求共享连接池
    db = SessionLocal()
    execution = None
    try:
        if target_date is None:
            target_date = get_trading_date()
        if target_date is None:
            raise ValueError("无法获取交易日，请指定target_date")
        target_date_str = target_date.strftime("%Y-%m-%d")
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 开始同步 {target_date} 的龙虎榜机构数据...")
        print(f"[{thread_name}] 开始同步 {target_date} 的龙虎榜机构数据...")
        
        # 延迟导入避免循环导入
        from app.services.task_service import TaskService
        from app.services.lhb_service import LhbService
        
        # 创建执行记录
        execution = TaskService.create_execution_record(
            db=db,
            task_name="龙虎榜机构数据同步",
            task_type="lhb_institution",
            triggered_by="scheduler",
            target_date=target_date_str,
        )
        execution.status = TaskStatus.RUNNING
        db.commit()
        
        execution_id = execution.id
        task_start_time = time.time()
        
        # 执行机构数据同步
        result = LhbService.sync_institution_data(db, target_date)
        
        task_duration = time.time() - task_start_time
        
        # 更新执行记录状态
        from app.services.task_service import make_json_serializable
        
        serializable_result = make_json_serializable({
            "success": result.success if isinstance(result, SyncResult) else result,
            "duration": f"{task_duration:.2f}",
            "message": str(result) if isinstance(result, SyncResult) else ("成功" if result else "失败"),
        })
        
        TaskService.update_execution_status(
            db=db,
            execution_id=execution_id,
            status=TaskStatus.SUCCESS if (result.success if isinstance(result, SyncResult) else result) else TaskStatus.FAILED,
            result=serializable_result,
            error_message=result.error if isinstance(result, SyncResult) and not result.success else None,
        )
        
        if result.success if isinstance(result, SyncResult) else result:
            logger.info(f"[{threading.current_thread().name}] ✅ 龙虎榜机构数据同步成功: {result} (耗时: {task_duration:.2f}秒)")
            print(f"✅ 龙虎榜机构数据同步成功: {result} (耗时: {task_duration:.2f}秒)")
        else:
            logger.error(f"[{threading.current_thread().name}] ❌ 龙虎榜机构数据同步失败: {result}")
            print(f"❌ 龙虎榜机构数据同步失败: {result}")
            
    except Exception as e:
        thread_name = threading.current_thread().name
        logger.error(f"[{thread_name}] 龙虎榜机构数据同步失败: {str(e)}", exc_info=True)
        print(f"[{thread_name}] 龙虎榜机构数据同步失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 更新执行记录状态为失败
        if execution:
            try:
                from app.services.task_service import TaskService
                TaskService.update_execution_status(
                    db=db,
                    execution_id=execution.id,
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                )
            except:
                pass
    finally:
        db.close()


def sync_institution_trading_statistics(target_date: date | None = None):
    """
    同步机构交易统计数据（从 stock_lhb_jgmmtj_em 获取）
    此任务在交易日收盘后执行（15:30）
    
    Args:
        target_date: 目标日期，None表示使用交易日
    """
    # 使用独立的数据库连接，避免与API请求共享连接池
    db = SessionLocal()
    execution = None
    try:
        if target_date is None:
            target_date = get_trading_date()
        if target_date is None:
            raise ValueError("无法获取交易日，请指定target_date")
        target_date_str = target_date.strftime("%Y-%m-%d")
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 开始同步 {target_date} 的机构交易统计数据...")
        print(f"[{thread_name}] 开始同步 {target_date} 的机构交易统计数据...")
        
        # 延迟导入避免循环导入
        from app.services.task_service import TaskService
        from app.services.institution_trading_service import InstitutionTradingService
        
        # 创建执行记录
        execution = TaskService.create_execution_record(
            db=db,
            task_name="机构交易统计数据同步",
            task_type="institution_trading_statistics",
            triggered_by="scheduler",
            target_date=target_date_str,
        )
        execution.status = TaskStatus.RUNNING
        db.commit()
        
        execution_id = execution.id
        task_start_time = time.time()
        
        # 执行机构交易统计数据同步
        result = InstitutionTradingService.sync_data(db, target_date)
        
        task_duration = time.time() - task_start_time
        
        # 更新执行记录状态
        from app.services.task_service import make_json_serializable
        
        serializable_result = make_json_serializable({
            "success": result.success if isinstance(result, SyncResult) else result,
            "duration": f"{task_duration:.2f}",
            "message": str(result) if isinstance(result, SyncResult) else ("成功" if result else "失败"),
        })
        
        TaskService.update_execution_status(
            db=db,
            execution_id=execution_id,
            status=TaskStatus.SUCCESS if (result.success if isinstance(result, SyncResult) else result) else TaskStatus.FAILED,
            result=serializable_result,
            error_message=result.error if isinstance(result, SyncResult) and not result.success else None,
        )
        
        if result.success if isinstance(result, SyncResult) else result:
            logger.info(f"[{threading.current_thread().name}] ✅ 机构交易统计数据同步成功: {result} (耗时: {task_duration:.2f}秒)")
            print(f"✅ 机构交易统计数据同步成功: {result} (耗时: {task_duration:.2f}秒)")
        else:
            logger.error(f"[{threading.current_thread().name}] ❌ 机构交易统计数据同步失败: {result}")
            print(f"❌ 机构交易统计数据同步失败: {result}")
            
    except Exception as e:
        thread_name = threading.current_thread().name
        logger.error(f"[{thread_name}] 机构交易统计数据同步失败: {str(e)}", exc_info=True)
        print(f"[{thread_name}] 机构交易统计数据同步失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 更新执行记录状态为失败
        if execution:
            try:
                from app.services.task_service import TaskService
                TaskService.update_execution_status(
                    db=db,
                    execution_id=execution.id,
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                )
            except:
                pass
    finally:
        db.close()


def sync_active_branch_data(target_date: date | None = None):
    """
    同步活跃营业部数据（从 stock_lhb_hyyyb_em 获取）
    此任务在北京时间4点执行
    
    Args:
        target_date: 目标日期，None表示使用交易日
    """
    # 使用独立的数据库连接，避免与API请求共享连接池
    db = SessionLocal()
    execution = None
    try:
        if target_date is None:
            target_date = get_trading_date()
        if target_date is None:
            raise ValueError("无法获取交易日，请指定target_date")
        target_date_str = target_date.strftime("%Y-%m-%d")
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 开始同步 {target_date} 的活跃营业部数据...")
        print(f"[{thread_name}] 开始同步 {target_date} 的活跃营业部数据...")
        
        # 延迟导入避免循环导入
        from app.services.task_service import TaskService
        from app.services.active_branch_service import ActiveBranchService
        
        # 创建执行记录
        execution = TaskService.create_execution_record(
            db=db,
            task_name="活跃营业部数据同步",
            task_type="active_branch",
            triggered_by="scheduler",
            target_date=target_date_str,
        )
        execution.status = TaskStatus.RUNNING
        db.commit()
        
        execution_id = execution.id
        task_start_time = time.time()
        
        # 执行活跃营业部数据同步
        result = ActiveBranchService.sync_data(db, target_date)
        
        task_duration = time.time() - task_start_time
        
        # 更新执行记录状态
        from app.services.task_service import make_json_serializable
        
        serializable_result = make_json_serializable({
            "success": result.success if isinstance(result, SyncResult) else result,
            "duration": f"{task_duration:.2f}",
            "message": str(result) if isinstance(result, SyncResult) else ("成功" if result else "失败"),
        })
        
        TaskService.update_execution_status(
            db=db,
            execution_id=execution_id,
            status=TaskStatus.SUCCESS if (result.success if isinstance(result, SyncResult) else result) else TaskStatus.FAILED,
            result=serializable_result,
            error_message=result.error if isinstance(result, SyncResult) and not result.success else None,
        )
        
        if result.success if isinstance(result, SyncResult) else result:
            logger.info(f"[{threading.current_thread().name}] ✅ 活跃营业部数据同步成功: {result} (耗时: {task_duration:.2f}秒)")
            print(f"✅ 活跃营业部数据同步成功: {result} (耗时: {task_duration:.2f}秒)")
        else:
            logger.error(f"[{threading.current_thread().name}] ❌ 活跃营业部数据同步失败: {result}")
            print(f"❌ 活跃营业部数据同步失败: {result}")
            
    except Exception as e:
        thread_name = threading.current_thread().name
        logger.error(f"[{thread_name}] 活跃营业部数据同步失败: {str(e)}", exc_info=True)
        print(f"[{thread_name}] 活跃营业部数据同步失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 更新执行记录状态为失败
        if execution:
            try:
                from app.services.task_service import TaskService
                TaskService.update_execution_status(
                    db=db,
                    execution_id=execution.id,
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                )
            except:
                pass
    finally:
        db.close()


def sync_active_branch_detail_data(target_date: date | None = None):
    """
    同步活跃营业部交易详情数据（从 stock_lhb_yyb_detail_em 获取）
    只同步2026年1月1日及之后的数据
    此任务在北京时间4:30执行（在活跃营业部数据同步之后）
    
    只同步卖出个股数量前10的活跃营业部，按照卖出个数降序排序，优先获取卖出最多的营业部
    
    Args:
        target_date: 目标日期，None表示使用交易日
    """
    # 使用独立的数据库连接，避免与API请求共享连接池
    db = SessionLocal()
    execution = None
    try:
        if target_date is None:
            target_date = get_trading_date()
        if target_date is None:
            raise ValueError("无法获取交易日，请指定target_date")
        
        # 只同步2026年1月1日及之后的数据
        from app.services.active_branch_detail_service import ActiveBranchDetailService
        if not ActiveBranchDetailService.should_store_data(target_date):
            logger.info(f"日期 {target_date} 早于存储起始日期，跳过同步")
            return
        
        target_date_str = target_date.strftime("%Y-%m-%d")
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 开始同步 {target_date} 的活跃营业部交易详情数据...")
        print(f"[{thread_name}] 开始同步 {target_date} 的活跃营业部交易详情数据...")
        
        # 延迟导入避免循环导入
        from app.services.task_service import TaskService
        
        # 创建执行记录
        execution = TaskService.create_execution_record(
            db=db,
            task_name="活跃营业部交易详情数据同步",
            task_type="active_branch_detail",
            triggered_by="scheduler",
            target_date=target_date_str,
        )
        execution.status = TaskStatus.RUNNING
        db.commit()
        
        execution_id = execution.id
        task_start_time = time.time()
        
        # 执行活跃营业部交易详情数据同步
        result = ActiveBranchDetailService.sync_date_data(db, target_date)
        
        task_duration = time.time() - task_start_time
        
        # 更新执行记录状态
        from app.services.task_service import make_json_serializable
        
        serializable_result = make_json_serializable({
            "success": result.success,
            "saved_count": result.count,
            "message": result.message,
            "duration": f"{task_duration:.2f}",
        })
        
        execution.status = TaskStatus.SUCCESS if result.success else TaskStatus.FAILED
        execution.result = serializable_result
        execution.duration = task_duration
        db.commit()
        
        logger.info(f"[{thread_name}] 活跃营业部交易详情数据同步完成，保存 {result.count} 条记录，耗时 {task_duration:.2f} 秒")
        print(f"[{thread_name}] 活跃营业部交易详情数据同步完成，保存 {result.count} 条记录，耗时 {task_duration:.2f} 秒")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"同步活跃营业部交易详情数据失败: {error_msg}")
        print(f"同步活跃营业部交易详情数据失败: {error_msg}")
        import traceback
        traceback.print_exc()
        
        if execution:
            try:
                execution.status = TaskStatus.FAILED
                execution.result = {"error": error_msg}
                db.commit()
            except Exception as commit_error:
                logger.error(f"更新执行记录失败: {str(commit_error)}")
                db.rollback()
    finally:
        db.close()


def sync_limit_up_stocks_history(target_date: date | None = None):
    """
    同步涨停股的历史行情数据（3个月）
    此任务应在涨停板数据同步之后执行
    
    Args:
        target_date: 目标日期，None表示使用交易日
    """
    # 使用独立的数据库连接，避免与API请求共享连接池
    db = SessionLocal()
    execution = None
    try:
        if target_date is None:
            target_date = get_trading_date()
        if target_date is None:
            raise ValueError("无法获取交易日，请指定target_date")
        target_date_str = target_date.strftime("%Y-%m-%d")
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 开始同步 {target_date} 的涨停股历史行情数据...")
        print(f"[{thread_name}] 开始同步 {target_date} 的涨停股历史行情数据...")
        
        # 延迟导入避免循环导入
        from app.services.task_service import TaskService
        from app.services.stock_history_service import StockHistoryService
        
        # 创建执行记录
        execution = TaskService.create_execution_record(
            db=db,
            task_name="涨停股历史行情数据同步",
            task_type="stock_history",
            triggered_by="scheduler",
            target_date=target_date_str,
        )
        execution.status = TaskStatus.RUNNING
        db.commit()
        
        execution_id = execution.id
        task_start_time = time.time()
        
        # 执行历史行情数据同步（3个月）
        result = StockHistoryService.sync_limit_up_stocks_history(db, target_date, months=3)
        
        task_duration = time.time() - task_start_time
        
        # 更新执行记录状态
        from app.services.task_service import make_json_serializable
        
        serializable_result = make_json_serializable({
            "success": result.success if isinstance(result, SyncResult) else result,
            "duration": f"{task_duration:.2f}",
            "message": str(result) if isinstance(result, SyncResult) else ("成功" if result else "失败"),
            "count": result.count if isinstance(result, SyncResult) else 0,
        })
        
        TaskService.update_execution_status(
            db=db,
            execution_id=execution_id,
            status=TaskStatus.SUCCESS if (result.success if isinstance(result, SyncResult) else result) else TaskStatus.FAILED,
            result=serializable_result,
            error_message=result.error if isinstance(result, SyncResult) and not result.success else None,
        )
        
        if result.success if isinstance(result, SyncResult) else result:
            logger.info(f"[{threading.current_thread().name}] ✅ 涨停股历史行情数据同步成功: {result} (耗时: {task_duration:.2f}秒)")
            print(f"✅ 涨停股历史行情数据同步成功: {result} (耗时: {task_duration:.2f}秒)")
        else:
            logger.error(f"[{threading.current_thread().name}] ❌ 涨停股历史行情数据同步失败: {result}")
            print(f"❌ 涨停股历史行情数据同步失败: {result}")
            
    except Exception as e:
        thread_name = threading.current_thread().name
        logger.error(f"[{thread_name}] 涨停股历史行情数据同步失败: {str(e)}", exc_info=True)
        print(f"[{thread_name}] 涨停股历史行情数据同步失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 更新执行记录状态为失败
        if execution:
            try:
                from app.services.task_service import TaskService
                TaskService.update_execution_status(
                    db=db,
                    execution_id=execution.id,
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                )
            except:
                pass
    finally:
        db.close()


# 全局调度器实例
_scheduler_instance: Optional[BackgroundScheduler] = None


def init_scheduler():
    """
    初始化调度器（性能优化版本）
    使用线程池执行器隔离任务执行，避免影响API响应时间
    """
    global _scheduler_instance
    
    # 使用北京时间
    beijing_tz = timezone("Asia/Shanghai")
    
    # 配置执行器：使用独立的线程池执行定时任务
    executors = {
        'default': TASK_EXECUTOR,
    }
    
    # 配置作业存储和执行器
    job_defaults = {
        'coalesce': True,  # 合并多个待执行的任务
        'max_instances': 1,  # 同一任务最多1个实例同时运行，避免重复执行
        'misfire_grace_time': 300,  # 任务错过执行时间后，5分钟内仍可执行
    }
    
    scheduler = BackgroundScheduler(
        timezone=beijing_tz,
        executors=executors,
        job_defaults=job_defaults
    )
    
    # 每日收盘后执行数据同步（北京时间 16:00）
    scheduler.add_job(
        sync_daily_data,
        trigger=CronTrigger(hour=16, minute=0, timezone=beijing_tz),
        id='sync_daily_data',
        name='每日数据同步',
        replace_existing=True,
        executor='default',  # 使用配置的线程池执行器
    )
    
    # 龙虎榜机构数据同步（北京时间 16:30，在基础数据同步之后）
    scheduler.add_job(
        sync_lhb_institution_data,
        trigger=CronTrigger(hour=16, minute=30, timezone=beijing_tz),
        id='sync_lhb_institution_data',
        name='龙虎榜机构数据同步',
        replace_existing=True,
        executor='default',  # 使用配置的线程池执行器
    )
    
    # 机构交易统计数据同步（北京时间 15:30，交易日收盘后）
    scheduler.add_job(
        sync_institution_trading_statistics,
        trigger=CronTrigger(hour=15, minute=30, timezone=beijing_tz),
        id='sync_institution_trading_statistics',
        name='机构交易统计数据同步',
        replace_existing=True,
        executor='default',  # 使用配置的线程池执行器
    )
    
    # 涨停股历史行情数据同步（北京时间 17:00，在涨停板数据同步之后）
    scheduler.add_job(
        sync_limit_up_stocks_history,
        trigger=CronTrigger(hour=17, minute=0, timezone=beijing_tz),
        id='sync_limit_up_stocks_history',
        name='涨停股历史行情数据同步',
        replace_existing=True,
        executor='default',  # 使用配置的线程池执行器
    )
    
    # 活跃营业部数据同步（北京时间 4:00）
    scheduler.add_job(
        sync_active_branch_data,
        trigger=CronTrigger(hour=4, minute=0, timezone=beijing_tz),
        id='sync_active_branch_data',
        name='活跃营业部数据同步',
        replace_existing=True,
        executor='default',  # 使用配置的线程池执行器
    )
    
    # 活跃营业部交易详情数据同步（北京时间 4:30，在活跃营业部数据同步之后）
    scheduler.add_job(
        sync_active_branch_detail_data,
        trigger=CronTrigger(hour=4, minute=30, timezone=beijing_tz),
        id='sync_active_branch_detail_data',
        name='活跃营业部交易详情数据同步',
        replace_existing=True,
        executor='default',  # 使用配置的线程池执行器
    )
    
    _scheduler_instance = scheduler
    return scheduler


def get_scheduler() -> Optional[BackgroundScheduler]:
    """获取全局调度器实例"""
    return _scheduler_instance


def get_scheduler_status() -> dict:
    """获取调度器状态信息"""
    scheduler = get_scheduler()
    
    if not scheduler:
        return {
            "running": False,
            "state": "not_initialized",
            "message": "调度器未初始化",
            "jobs": [],
            "job_count": 0
        }
    
    jobs_info = []
    for job in scheduler.get_jobs():
        # 获取下次执行时间
        next_run_time = None
        try:
            # APScheduler 3.x 使用 next_run_time 属性
            if hasattr(job, 'next_run_time'):
                next_run_time = job.next_run_time
            # 如果调度器正在运行，尝试计算下次执行时间
            elif scheduler.running and job.trigger:
                try:
                    next_run_time = job.trigger.get_next_fire_time(None, datetime.now(scheduler.timezone))
                except:
                    pass
        except Exception:
            pass
        
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": next_run_time.isoformat() if next_run_time else None,
            "next_run_time_str": next_run_time.strftime("%Y-%m-%d %H:%M:%S") if next_run_time else None,
            "trigger": str(job.trigger),
            "func": job.func.__name__ if hasattr(job.func, '__name__') else str(job.func),
        })
    
    return {
        "running": scheduler.running,
        "state": "running" if scheduler.running else "stopped",
        "jobs": jobs_info,
        "job_count": len(jobs_info),
        "message": None
    }


def sync_daily_data(task_types: list[str] | None = None, target_date: date | None = None, execution_id: int | None = None):
    """
    同步每日数据
    调用各个服务的数据同步方法
    
    注意：此函数在独立的线程中执行，不会阻塞API请求
    
    Args:
        task_types: 要执行的任务类型列表，None表示执行所有任务
        target_date: 目标日期，None表示使用交易日
        execution_id: 已存在的执行记录ID，如果提供则使用现有记录，否则创建新记录
    """
    # 使用独立的数据库连接，避免与API请求共享连接池
    # 这样可以确保任务执行不会占用API请求的连接资源
    db = SessionLocal()
    execution = None
    try:
        if target_date is None:
            target_date = get_trading_date()
        if target_date is None:
            raise ValueError("无法获取交易日，请指定target_date")
        target_date_str = target_date.strftime("%Y-%m-%d")
        thread_name = threading.current_thread().name
        logger.info(f"[{thread_name}] 开始同步 {target_date} 的数据...")
        print(f"[{thread_name}] 开始同步 {target_date} 的数据...")
        
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
        from app.services.institution_trading_service import InstitutionTradingService
        from app.services.active_branch_service import ActiveBranchService
        from app.services.active_branch_detail_service import ActiveBranchDetailService
        from app.services.zt_pool_service import ZtPoolService
        from app.services.zt_pool_service import ZtPoolDownService
        from app.services.index_service import IndexService
        from app.services.fund_flow_service import FundFlowService
        from app.services.capital_service import CapitalService
        from app.services.stock_history_service import StockHistoryService
        
        # 任务映射：key -> (service_method, 是否需要独立db连接)
        # 注意：所有任务方法都需要db参数，并行执行时会使用独立连接
        task_map = {
            "lhb": (LhbService.sync_data, True),
            "lhb_institution": (LhbService.sync_institution_data, True),
            "institution_trading_statistics": (InstitutionTradingService.sync_data, True),
            "active_branch": (ActiveBranchService.sync_data, True),
            "active_branch_detail": (ActiveBranchDetailService.sync_date_data, True),
            "zt_pool": (ZtPoolService.sync_data, True),
            "zt_pool_down": (ZtPoolDownService.sync_data, True),
            "index": (IndexService.sync_data, True),
            "stock_fund_flow": (FundFlowService.sync_data, True),
            "fund_flow_concept": (lambda db, date: FundFlowService.sync_concept_fund_flow(db, date, limit=200), True),
            "capital": (CapitalService.sync_data, True),
            "stock_history": (lambda db, date: StockHistoryService.sync_limit_up_stocks_history(db, date, months=3), True),
        }

        selected_keys = task_types if task_types else list(task_map.keys())
        results = {}
        error_details = {}
        task_results = {}
        
        # 定义任务依赖关系：某些任务必须在其他任务完成后执行
        # 例如：lhb_institution 依赖 lhb，active_branch_detail 依赖 active_branch
        task_dependencies = {
            "lhb_institution": ["lhb"],  # 龙虎榜机构数据依赖龙虎榜基础数据
            "active_branch_detail": ["active_branch"],  # 活跃营业部详情依赖活跃营业部数据
            "stock_history": ["zt_pool"],  # 涨停股历史行情依赖涨停池数据
        }
        
        # 分离独立任务和依赖任务
        independent_tasks = []
        dependent_tasks = []
        
        for key in selected_keys:
            if key in task_dependencies:
                # 检查依赖是否满足
                deps = task_dependencies[key]
                if all(dep in selected_keys for dep in deps):
                    dependent_tasks.append(key)
                else:
                    # 依赖不满足，跳过或标记为独立任务（如果依赖已完成）
                    independent_tasks.append(key)
            else:
                independent_tasks.append(key)
        
        # 定义执行单个任务的函数（使用独立数据库连接）
        def execute_task(key: str, service_method, target_date_param):
            """执行单个任务，使用独立的数据库连接"""
            task_db = SessionLocal()
            task_start_time = time.time()
            try:
                # 调用服务方法，传入独立的数据库连接和目标日期
                result = service_method(task_db, target_date_param)
                
                # 兼容旧代码：如果返回 bool，转换为 SyncResult
                if isinstance(result, bool):
                    if result:
                        result = SyncResult.success_result(f"{key} 同步成功")
                    else:
                        result = SyncResult.failure_result(f"{key} 同步失败", "返回 False")
                
                task_duration = time.time() - task_start_time
                return {
                    "key": key,
                    "result": result,
                    "duration": task_duration,
                    "success": result.success if isinstance(result, SyncResult) else result,
                }
            except Exception as e:
                task_duration = time.time() - task_start_time
                error_msg = f"{key} 执行异常: {str(e)}"
                logger.error(f"[{threading.current_thread().name}] ❌ {error_msg}", exc_info=True)
                import traceback
                traceback.print_exc()
                return {
                    "key": key,
                    "result": SyncResult.failure_result(str(e), error_msg),
                    "duration": task_duration,
                    "success": False,
                    "error": str(e),
                }
            finally:
                task_db.close()
        
        # 第一阶段：并行执行独立任务
        if independent_tasks:
            logger.info(f"[{thread_name}] 开始并行执行 {len(independent_tasks)} 个独立任务...")
            print(f"[{thread_name}] 开始并行执行 {len(independent_tasks)} 个独立任务...")
            
            # 使用线程池并行执行独立任务
            # 限制并发数，避免过多并发导致数据库连接池耗尽
            max_workers = min(len(independent_tasks), 5)  # 最多5个并发任务
            
            with ConcurrentThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for key in independent_tasks:
                    task_info = task_map.get(key)
                    if not task_info:
                        print(f"跳过未知任务: {key}")
                        error_details[key] = "未知任务类型"
                        continue
                    service_method, _ = task_info
                    # 提交任务，使用独立的数据库连接
                    futures[executor.submit(execute_task, key, service_method, target_date)] = key
                
                # 收集结果
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        task_result = future.result()
                        key = task_result["key"]
                        result = task_result["result"]
                        task_duration = task_result["duration"]
                        
                        results[key] = result
                        task_results[key] = {
                            "success": task_result["success"],
                            "duration": f"{task_duration:.2f}",
                            "message": str(result) if isinstance(result, SyncResult) else ("成功" if result else "失败"),
                        }
                        
                        # 打印详细结果
                        if task_result["success"]:
                            logger.info(f"[{threading.current_thread().name}] ✅ {key}: {result} (耗时: {task_duration:.2f}秒)")
                            print(f"✅ {key}: {result} (耗时: {task_duration:.2f}秒)")
                        else:
                            logger.error(f"[{threading.current_thread().name}] ❌ {key}: {result}")
                            print(f"❌ {key}: {result}")
                            error_details[key] = result.error if isinstance(result, SyncResult) else task_result.get("error", "未知错误")
                    except Exception as e:
                        logger.error(f"[{threading.current_thread().name}] ❌ 任务 {key} 执行异常: {str(e)}", exc_info=True)
                        error_details[key] = str(e)
        
        # 第二阶段：串行执行依赖任务（确保依赖已完成）
        if dependent_tasks:
            logger.info(f"[{thread_name}] 开始串行执行 {len(dependent_tasks)} 个依赖任务...")
            print(f"[{thread_name}] 开始串行执行 {len(dependent_tasks)} 个依赖任务...")
            
            for key in dependent_tasks:
                task_info = task_map.get(key)
                if not task_info:
                    print(f"跳过未知任务: {key}")
                    error_details[key] = "未知任务类型"
                    continue
                service_method, _ = task_info
                
                # 检查依赖是否成功
                deps = task_dependencies.get(key, [])
                if deps and not all(results.get(dep, SyncResult.failure_result("", "")).success if isinstance(results.get(dep), SyncResult) else results.get(dep, False) for dep in deps):
                    logger.warning(f"[{thread_name}] ⚠️ 跳过任务 {key}，因为依赖任务未成功完成")
                    print(f"⚠️ 跳过任务 {key}，因为依赖任务未成功完成")
                    results[key] = SyncResult.failure_result("依赖任务未成功", f"依赖任务 {deps} 未成功完成")
                    error_details[key] = f"依赖任务 {deps} 未成功完成"
                    continue
                
                task_result = execute_task(key, service_method, target_date)
                key = task_result["key"]
                result = task_result["result"]
                task_duration = task_result["duration"]
                
                results[key] = result
                task_results[key] = {
                    "success": task_result["success"],
                    "duration": f"{task_duration:.2f}",
                    "message": str(result) if isinstance(result, SyncResult) else ("成功" if result else "失败"),
                }
                
                # 打印详细结果
                if task_result["success"]:
                    logger.info(f"[{threading.current_thread().name}] ✅ {key}: {result} (耗时: {task_duration:.2f}秒)")
                    print(f"✅ {key}: {result} (耗时: {task_duration:.2f}秒)")
                else:
                    logger.error(f"[{threading.current_thread().name}] ❌ {key}: {result}")
                    print(f"❌ {key}: {result}")
                    error_details[key] = result.error if isinstance(result, SyncResult) else task_result.get("error", "未知错误")

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
        thread_name = threading.current_thread().name
        logger.error(f"[{thread_name}] 数据同步失败: {str(e)}", exc_info=True)
        print(f"[{thread_name}] 数据同步失败: {str(e)}")
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

