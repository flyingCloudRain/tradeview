"""
临时脚本：获取近期30个交易日的机构交易统计数据
"""
import sys
from pathlib import Path
from datetime import date, datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal
from app.services.institution_trading_service import InstitutionTradingService
import akshare as ak
import pandas as pd


def get_trading_dates(count: int = 30) -> list[date]:
    """
    获取最近N个交易日
    
    Args:
        count: 需要获取的交易日数量
        
    Returns:
        list[date]: 交易日列表（从新到旧）
    """
    try:
        # 获取交易日历（最近60天，确保能获取到30个交易日）
        end_date = date.today()
        start_date = end_date - timedelta(days=60)
        
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")
        
        print(f"[获取交易日历] 日期范围: {start_date_str} - {end_date_str}")
        
        # 调用 akshare 获取交易日历
        df = ak.tool_trade_date_hist_sina()
        
        if df is None or df.empty:
            print("⚠️  无法获取交易日历，使用简化方法")
            # 简化方法：排除周末
            trading_dates = []
            current_date = end_date
            while len(trading_dates) < count and current_date >= start_date:
                # 排除周末（周六=5, 周日=6）
                if current_date.weekday() < 5:
                    trading_dates.append(current_date)
                current_date -= timedelta(days=1)
            return trading_dates
        
        # 转换日期列
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
            df.rename(columns={'date': 'trade_date'}, inplace=True)
        else:
            print("⚠️  交易日历格式异常，使用简化方法")
            trading_dates = []
            current_date = end_date
            while len(trading_dates) < count and current_date >= start_date:
                if current_date.weekday() < 5:
                    trading_dates.append(current_date)
                current_date -= timedelta(days=1)
            return trading_dates
        
        # 过滤日期范围并排序
        df_filtered = df[
            (df['trade_date'] >= start_date) & 
            (df['trade_date'] <= end_date)
        ].sort_values('trade_date', ascending=False)
        
        # 获取最近的N个交易日
        trading_dates = df_filtered['trade_date'].head(count).tolist()
        
        print(f"[获取交易日历] 找到 {len(trading_dates)} 个交易日")
        return trading_dates
        
    except Exception as e:
        print(f"⚠️  获取交易日历失败: {str(e)}，使用简化方法")
        import traceback
        traceback.print_exc()
        
        # 简化方法：排除周末
        trading_dates = []
        current_date = end_date
        while len(trading_dates) < count and current_date >= start_date:
            if current_date.weekday() < 5:
                trading_dates.append(current_date)
            current_date -= timedelta(days=1)
        return trading_dates


def sync_institution_trading_statistics_for_dates(trading_dates: list[date], force: bool = False) -> dict:
    """
    同步多个交易日的机构交易统计数据
    
    Args:
        trading_dates: 交易日列表
        
    Returns:
        dict: 同步结果统计
    """
    db = SessionLocal()
    results = {
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'details': []
    }
    
    try:
        total_dates = len(trading_dates)
        print(f"\n{'='*60}")
        print(f"开始同步 {total_dates} 个交易日的机构交易统计数据")
        print(f"{'='*60}\n")
        
        for idx, target_date in enumerate(trading_dates, 1):
            date_str = target_date.strftime("%Y-%m-%d")
            print(f"[{idx}/{total_dates}] 同步 {date_str} 的数据...")
            
            try:
                # 检查是否已有数据（除非使用--force选项）
                if not force:
                    from app.models.lhb import InstitutionTradingStatistics
                    existing_count = db.query(InstitutionTradingStatistics).filter(
                        InstitutionTradingStatistics.date == target_date
                    ).count()
                    
                    if existing_count > 0:
                        print(f"  ⏭️  跳过（已有 {existing_count} 条数据）")
                        results['skipped'] += 1
                        results['details'].append({
                            'date': date_str,
                            'status': 'skipped',
                            'message': f'已有 {existing_count} 条数据'
                        })
                        continue
                
                # 执行同步
                result = InstitutionTradingService.sync_data(db, target_date)
                
                if result.success:
                    print(f"  ✅ 成功: {result.message}")
                    results['success'] += 1
                    results['details'].append({
                        'date': date_str,
                        'status': 'success',
                        'message': result.message
                    })
                else:
                    print(f"  ❌ 失败: {result.error_message}")
                    results['failed'] += 1
                    results['details'].append({
                        'date': date_str,
                        'status': 'failed',
                        'message': result.error_message
                    })
                
            except Exception as e:
                error_msg = str(e)
                print(f"  ❌ 异常: {error_msg}")
                results['failed'] += 1
                results['details'].append({
                    'date': date_str,
                    'status': 'error',
                    'message': error_msg
                })
                import traceback
                traceback.print_exc()
            
            # 每10个日期输出一次进度
            if idx % 10 == 0:
                print(f"\n进度: {idx}/{total_dates} ({idx*100//total_dates}%)")
                print(f"成功: {results['success']}, 失败: {results['failed']}, 跳过: {results['skipped']}\n")
        
        return results
        
    finally:
        db.close()


def get_trading_dates_by_range(start_date: date, end_date: date) -> list[date]:
    """
    获取指定日期范围内的交易日列表
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        list[date]: 交易日列表（从新到旧）
    """
    try:
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")
        
        print(f"[获取交易日历] 日期范围: {start_date_str} - {end_date_str}")
        
        # 调用 akshare 获取交易日历
        df = ak.tool_trade_date_hist_sina()
        
        if df is None or df.empty:
            print("⚠️  无法获取交易日历，使用简化方法")
            # 简化方法：排除周末
            trading_dates = []
            current_date = end_date
            while current_date >= start_date:
                # 排除周末（周六=5, 周日=6）
                if current_date.weekday() < 5:
                    trading_dates.append(current_date)
                current_date -= timedelta(days=1)
            return trading_dates
        
        # 转换日期列
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.date
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.date
            df.rename(columns={'date': 'trade_date'}, inplace=True)
        else:
            print("⚠️  交易日历格式异常，使用简化方法")
            trading_dates = []
            current_date = end_date
            while current_date >= start_date:
                if current_date.weekday() < 5:
                    trading_dates.append(current_date)
                current_date -= timedelta(days=1)
            return trading_dates
        
        # 过滤日期范围并排序
        df_filtered = df[
            (df['trade_date'] >= start_date) & 
            (df['trade_date'] <= end_date)
        ].sort_values('trade_date', ascending=False)
        
        # 获取交易日列表
        trading_dates = df_filtered['trade_date'].tolist()
        
        print(f"[获取交易日历] 找到 {len(trading_dates)} 个交易日")
        return trading_dates
        
    except Exception as e:
        print(f"⚠️  获取交易日历失败: {str(e)}，使用简化方法")
        import traceback
        traceback.print_exc()
        
        # 简化方法：排除周末
        trading_dates = []
        current_date = end_date
        while current_date >= start_date:
            if current_date.weekday() < 5:
                trading_dates.append(current_date)
            current_date -= timedelta(days=1)
        return trading_dates


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="获取机构交易统计数据")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="需要获取的交易日数量（与--start-date/--end-date互斥）"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="开始日期（格式：YYYY-MM-DD），与--end-date一起使用"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="结束日期（格式：YYYY-MM-DD），与--start-date一起使用"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制同步，即使已有数据也重新同步"
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="自动确认，跳过交互式确认"
    )
    
    args = parser.parse_args()
    
    # 获取交易日列表
    print("=" * 60)
    print("获取交易日历...")
    print("=" * 60)
    
    # 根据参数选择获取方式
    if args.start_date and args.end_date:
        # 日期范围模式
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
            
            if start_date > end_date:
                print("❌ 开始日期不能大于结束日期")
                sys.exit(1)
            
            trading_dates = get_trading_dates_by_range(start_date, end_date)
        except ValueError as e:
            print(f"❌ 日期格式错误: {e}，请使用 YYYY-MM-DD 格式")
            sys.exit(1)
    elif args.days:
        # 最近N天模式
        trading_dates = get_trading_dates(count=args.days)
    else:
        # 默认：最近30天
        trading_dates = get_trading_dates(count=30)
    
    if not trading_dates:
        print("❌ 无法获取交易日列表")
        sys.exit(1)
    
    print(f"\n将同步以下 {len(trading_dates)} 个交易日的数据：")
    for i, d in enumerate(trading_dates[:10], 1):
        print(f"  {i}. {d.strftime('%Y-%m-%d')}")
    if len(trading_dates) > 10:
        print(f"  ... 还有 {len(trading_dates) - 10} 个交易日")
    
    # 确认（除非使用--yes选项）
    if not args.yes:
        try:
            response = input(f"\n是否继续？(y/n): ")
            if response.lower() != 'y':
                print("已取消")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\n⚠️  检测到非交互式环境，使用 --yes 选项可跳过确认")
            print("已取消")
            sys.exit(0)
    
    # 执行同步
    results = sync_institution_trading_statistics_for_dates(trading_dates, force=args.force)
    
    # 输出结果汇总
    print(f"\n{'='*60}")
    print("同步完成！")
    print(f"{'='*60}")
    print(f"总计: {len(trading_dates)} 个交易日")
    print(f"成功: {results['success']} 个")
    print(f"失败: {results['failed']} 个")
    print(f"跳过: {results['skipped']} 个")
    
    if results['failed'] > 0:
        print(f"\n失败的日期：")
        for detail in results['details']:
            if detail['status'] in ['failed', 'error']:
                print(f"  - {detail['date']}: {detail['message']}")
    
    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
