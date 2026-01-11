"""
手动执行定时任务脚本
支持指定任务类型和日期
"""
import sys
from pathlib import Path
from datetime import date, datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tasks.scheduler import sync_daily_data
from app.utils.date_utils import get_trading_date


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="手动执行定时任务")
    parser.add_argument(
        "--tasks",
        type=str,
        nargs="+",
        help="要执行的任务类型，可选: zt_pool, stock_fund_flow, index, fund_flow_concept 等。不指定则执行所有任务",
        default=["zt_pool", "stock_fund_flow", "index", "fund_flow_concept"]
    )
    parser.add_argument(
        "--date",
        type=str,
        help="指定日期 (格式: YYYY-MM-DD)，不指定则使用交易日",
    )
    
    args = parser.parse_args()
    
    # 解析日期
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ 日期格式错误: {args.date}，请使用 YYYY-MM-DD 格式")
            sys.exit(1)
    else:
        target_date = get_trading_date()
        if not target_date:
            print("❌ 无法获取交易日，请使用 --date 参数指定日期")
            sys.exit(1)
    
    print("=" * 60)
    print(f"开始执行定时任务 - 日期: {target_date}")
    print(f"任务类型: {', '.join(args.tasks)}")
    print("=" * 60)
    
    # 执行任务
    try:
        sync_daily_data(task_types=args.tasks)
        print("\n✅ 任务执行完成！")
    except Exception as e:
        print(f"\n❌ 任务执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

