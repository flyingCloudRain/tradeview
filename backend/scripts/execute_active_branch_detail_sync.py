"""
手动执行活跃营业部交易详情数据同步任务
"""
import sys
from pathlib import Path
from datetime import date

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tasks.scheduler import sync_active_branch_detail_data


def main():
    """执行2026年1月16日的数据同步"""
    target_date = date(2026, 1, 16)
    
    print("=" * 80)
    print(f"开始执行活跃营业部交易详情数据同步任务")
    print(f"目标日期: {target_date}")
    print("=" * 80)
    print()
    
    try:
        # 执行任务
        sync_active_branch_detail_data(target_date=target_date)
        print()
        print("=" * 80)
        print("✅ 任务执行完成！")
        print("=" * 80)
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ 任务执行失败: {str(e)}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
