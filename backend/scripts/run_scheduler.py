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
    print("✅ 调度器已启动 (APS cheduler)")

    try:
        # 阻塞保持进程存活
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("⏹️ 收到退出信号，停止调度器...")
    finally:
        scheduler.shutdown()
        print("🛑 调度器已停止")


if __name__ == "__main__":
    main()

