#!/usr/bin/env python3
"""
检查定时任务执行情况的脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal
from app.models.task_execution import TaskExecution, TaskStatus
from app.tasks.scheduler import get_scheduler_status
from sqlalchemy import desc, func, and_
from datetime import datetime, timedelta
import pytz

def check_scheduler_status():
    """检查调度器运行状态"""
    print("=" * 80)
    print("调度器运行状态检查")
    print("=" * 80)
    
    status = get_scheduler_status()
    
    if status['state'] == 'not_initialized':
        print("\n❌ 调度器未初始化")
        print("   请启动调度器: python backend/scripts/run_scheduler.py")
        return False
    elif status['state'] == 'stopped':
        print("\n⚠️  调度器已停止")
        print("   请启动调度器: python backend/scripts/run_scheduler.py")
        return False
    elif status['state'] == 'running':
        print(f"\n✅ 调度器正在运行")
        print(f"   任务数量: {status['job_count']}")
        
        if status['jobs']:
            print("\n   定时任务列表:")
            for job in status['jobs']:
                next_run = job.get('next_run_time_str') or "未安排"
                print(f"     - {job['name']} ({job['id']})")
                print(f"       下次执行: {next_run}")
        
        return True
    
    return False


def check_task_executions():
    """检查任务执行历史"""
    db = SessionLocal()
    beijing_tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(beijing_tz)
    today = now.date()
    
    print("\n" + "=" * 80)
    print("任务执行历史分析")
    print("=" * 80)
    print(f"当前时间（北京时间）: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 获取所有调度器任务
    scheduler_tasks = db.query(TaskExecution).filter(
        TaskExecution.triggered_by == "scheduler"
    ).order_by(desc(TaskExecution.start_time)).all()
    
    print(f"调度器任务总数: {len(scheduler_tasks)}")
    
    if len(scheduler_tasks) == 0:
        print("\n⚠️  警告: 没有找到任何调度器任务记录！")
        print("   这说明调度器可能从未启动过，或者启动后没有执行过任务")
        db.close()
        return
    
    # 检查今天的任务
    today_tasks = db.query(TaskExecution).filter(
        and_(
            TaskExecution.triggered_by == "scheduler",
            func.date(TaskExecution.start_time) == today
        )
    ).all()
    
    print(f"\n今天的调度器任务: {len(today_tasks)} 条")
    
    if len(today_tasks) == 0:
        expected_daily_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
        expected_lhb_time = now.replace(hour=16, minute=30, second=0, microsecond=0)
        
        if now.hour >= 16:
            print(f"\n❌ 警告: 今天还没有执行调度器任务！")
            print(f"   每日数据同步应该在 {expected_daily_time.strftime('%H:%M')} 执行")
            print(f"   龙虎榜机构数据同步应该在 {expected_lhb_time.strftime('%H:%M')} 执行")
        else:
            print(f"\nℹ️  今天还未到执行时间（当前 {now.strftime('%H:%M')}）")
    else:
        print("\n今天的任务执行记录:")
        for task in today_tasks:
            task_time = task.start_time.astimezone(beijing_tz)
            status_icon = "✅" if task.status == TaskStatus.SUCCESS else "❌" if task.status == TaskStatus.FAILED else "⏳"
            print(f"  {status_icon} {task.task_name} ({task.task_type})")
            print(f"     时间: {task_time.strftime('%H:%M:%S')}")
            print(f"     状态: {task.status.value}")
            if task.duration:
                print(f"     耗时: {task.duration}秒")
    
    # 分析最近的任务执行情况
    print(f"\n最近 {min(10, len(scheduler_tasks))} 条调度器任务:")
    
    # 每日数据同步任务分析
    daily_tasks = [t for t in scheduler_tasks if t.task_type == "all" or "每日数据同步" in t.task_name]
    if daily_tasks:
        print(f"\n每日数据同步任务（应于16:00执行）:")
        on_time = 0
        late = 0
        
        for task in daily_tasks[:10]:
            task_time = task.start_time.astimezone(beijing_tz)
            expected_time = task_time.replace(hour=16, minute=0, second=0, microsecond=0)
            time_diff = (task_time - expected_time).total_seconds() / 60
            
            is_on_time = abs(time_diff) <= 5
            if is_on_time:
                on_time += 1
            elif time_diff > 5:
                late += 1
            
            icon = "✅" if is_on_time else "⚠️"
            diff_str = f"{int(abs(time_diff))}分钟" if abs(time_diff) >= 1 else f"{int(abs(time_diff)*60)}秒"
            late_str = "延迟" if time_diff > 0 else "提前"
            
            print(f"  {icon} {task_time.strftime('%Y-%m-%d %H:%M:%S')} - "
                  f"预期: 16:00, 实际: {task_time.strftime('%H:%M')}, "
                  f"{late_str} {diff_str}, 状态: {task.status.value}")
        
        print(f"  统计: 按时 {on_time}/{len(daily_tasks)}, 延迟 {late}/{len(daily_tasks)}")
    
    # 龙虎榜机构数据同步分析
    lhb_tasks = [t for t in scheduler_tasks if "lhb_institution" in t.task_type or "龙虎榜机构" in t.task_name]
    if lhb_tasks:
        print(f"\n龙虎榜机构数据同步任务（应于16:30执行）:")
        on_time = 0
        late = 0
        
        for task in lhb_tasks[:10]:
            task_time = task.start_time.astimezone(beijing_tz)
            expected_time = task_time.replace(hour=16, minute=30, second=0, microsecond=0)
            time_diff = (task_time - expected_time).total_seconds() / 60
            
            is_on_time = abs(time_diff) <= 5
            if is_on_time:
                on_time += 1
            elif time_diff > 5:
                late += 1
            
            icon = "✅" if is_on_time else "⚠️"
            diff_str = f"{int(abs(time_diff))}分钟" if abs(time_diff) >= 1 else f"{int(abs(time_diff)*60)}秒"
            late_str = "延迟" if time_diff > 0 else "提前"
            
            print(f"  {icon} {task_time.strftime('%Y-%m-%d %H:%M:%S')} - "
                  f"预期: 16:30, 实际: {task_time.strftime('%H:%M')}, "
                  f"{late_str} {diff_str}, 状态: {task.status.value}")
        
        print(f"  统计: 按时 {on_time}/{len(lhb_tasks)}, 延迟 {late}/{len(lhb_tasks)}")
    
    db.close()


def main():
    """主函数"""
    scheduler_running = check_scheduler_status()
    check_task_executions()
    
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    
    if not scheduler_running:
        print("\n❌ 调度器未运行，定时任务不会自动执行")
        print("\n启动调度器:")
        print("  cd backend")
        print("  python scripts/run_scheduler.py")
        print("\n或者使用后台运行:")
        print("  nohup python scripts/run_scheduler.py > ../logs/scheduler.log 2>&1 &")
    else:
        print("\n✅ 调度器正在运行，定时任务会按计划执行")
        print("\n查看调度器状态:")
        print("  curl http://localhost:8000/api/v1/tasks/scheduler/status")


if __name__ == "__main__":
    main()
