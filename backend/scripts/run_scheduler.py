"""
独立启动 APScheduler 调度器的入口。
运行方式（项目根目录）:
  python backend/scripts/run_scheduler.py
"""
import sys
from pathlib import Path
import time

# 将项目根目录加入路径，便于独立执行
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tasks.scheduler import init_scheduler


def main():
    scheduler = init_scheduler()
    scheduler.start()
    print("✅ 调度器已启动 (APScheduler)")
    
    # 打印调度器状态
    from app.tasks.scheduler import get_scheduler_status
    status = get_scheduler_status()
    print(f"\n📋 调度器状态:")
    print(f"  运行状态: {'运行中' if status['running'] else '已停止'}")
    print(f"  任务数量: {status['job_count']}")
    print(f"\n📅 定时任务列表:")
    for job in status['jobs']:
        next_run = job['next_run_time_str'] or "未安排"
        print(f"  - {job['name']} ({job['id']})")
        print(f"    下次执行: {next_run}")
        print(f"    触发器: {job['trigger']}")

    try:
        # 阻塞保持进程存活
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n⏹️ 收到退出信号，停止调度器...")
    finally:
        scheduler.shutdown()
        print("🛑 调度器已停止")


if __name__ == "__main__":
    main()

