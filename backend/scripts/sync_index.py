"""
手动同步指数数据脚本
"""
import sys
from pathlib import Path
from datetime import date

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal
from app.services.index_service import IndexService
from app.utils.date_utils import get_trading_date


def sync_index_data(target_date: date = None):
    """同步指数数据"""
    if target_date is None:
        target_date = get_trading_date()
    
    print("=" * 60)
    print(f"开始同步指数数据 - 日期: {target_date}")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        success = IndexService.sync_data(db, target_date)
        
        if success:
            print(f"\n✅ 指数数据同步成功！")
            
            # 查询同步的数据
            index_list = IndexService.get_index_list(db, target_date)
            print(f"\n📊 已同步 {len(index_list)} 条指数数据：")
            for idx in index_list[:10]:  # 显示前10条
                print(f"  - {idx.index_name} ({idx.index_code}): {idx.close_price or 'N/A'}, "
                      f"涨跌幅: {idx.change_percent or 'N/A'}%")
            if len(index_list) > 10:
                print(f"  ... 还有 {len(index_list) - 10} 条数据")
        else:
            print(f"\n❌ 指数数据同步失败！")
            return False
            
    except Exception as e:
        print(f"\n❌ 同步过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    print("=" * 60)
    return success


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="手动同步指数数据")
    parser.add_argument(
        "--date",
        type=str,
        help="指定日期 (格式: YYYY-MM-DD)，不指定则使用交易日",
    )
    
    args = parser.parse_args()
    
    target_date = None
    if args.date:
        from datetime import datetime
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ 日期格式错误: {args.date}，请使用 YYYY-MM-DD 格式")
            sys.exit(1)
    
    success = sync_index_data(target_date)
    sys.exit(0 if success else 1)

