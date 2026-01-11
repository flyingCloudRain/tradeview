"""
同步龙虎榜个股交易机构数据脚本
"""
import sys
from pathlib import Path
from datetime import date, datetime
import time

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal
from app.models.lhb import LhbDetail, LhbInstitution
from app.services.lhb_service import LhbService
from app.utils.akshare_utils import safe_akshare_call
import akshare as ak


def sync_institutions_for_date(target_date: date, limit: int = None):
    """同步指定日期的所有股票的机构明细数据"""
    print("=" * 70)
    print(f"同步 {target_date} 龙虎榜个股交易机构数据")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        # 获取该日期的所有龙虎榜股票
        lhb_details = db.query(LhbDetail).filter(LhbDetail.date == target_date).all()
        
        if not lhb_details:
            print(f"❌ 未找到 {target_date} 的龙虎榜基础数据，请先同步基础数据")
            return False
        
        print(f"\n📋 共 {len(lhb_details)} 只股票需要同步机构数据\n")
        
        date_str = target_date.strftime("%Y%m%d")
        success_count = 0
        fail_count = 0
        total_institutions = 0
        
        # 限制处理数量（用于测试）
        if limit:
            lhb_details = lhb_details[:limit]
            print(f"⚠️  限制处理前 {limit} 只股票\n")
        
        for i, lhb_detail in enumerate(lhb_details, 1):
            stock_code = lhb_detail.stock_code
            stock_name = lhb_detail.stock_name
            
            print(f"[{i}/{len(lhb_details)}] {stock_code} {stock_name} - ", end="", flush=True)
            
            try:
                # 获取买入机构
                df_buy = safe_akshare_call(
                    ak.stock_lhb_stock_detail_em,
                    symbol=stock_code,
                    date=date_str,
                    flag='买入'
                )
                
                # 获取卖出机构
                df_sell = safe_akshare_call(
                    ak.stock_lhb_stock_detail_em,
                    symbol=stock_code,
                    date=date_str,
                    flag='卖出'
                )
                
                if df_buy is None and df_sell is None:
                    print("❌ 未获取到机构数据")
                    fail_count += 1
                    continue
                
                # 保存机构数据
                inst_count = LhbService.save_institution_data(
                    db, lhb_detail.id, stock_code, target_date, df_buy, df_sell
                )
                
                if inst_count > 0:
                    print(f"✅ 成功 ({inst_count} 条机构)")
                    success_count += 1
                    total_institutions += inst_count
                else:
                    print("⚠️  无机构数据")
                    fail_count += 1
                
                # 避免请求过快
                if i < len(lhb_details):
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"❌ 错误: {str(e)[:50]}")
                fail_count += 1
                continue
        
        # 输出统计结果
        print()
        print("=" * 70)
        print("📊 同步结果统计")
        print("=" * 70)
        print(f"✅ 成功: {success_count} 只股票")
        print(f"❌ 失败: {fail_count} 只股票")
        print(f"📈 总机构记录数: {total_institutions} 条")
        print("=" * 70)
        
        return success_count > 0
        
    except Exception as e:
        print(f"\n❌ 同步过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def show_institutions_for_date(target_date: date, limit: int = 10):
    """显示指定日期的机构数据"""
    print("=" * 70)
    print(f"显示 {target_date} 龙虎榜个股交易机构数据")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        # 获取有机构数据的股票
        lhb_details = db.query(LhbDetail).filter(
            LhbDetail.date == target_date
        ).join(LhbInstitution).distinct().limit(limit).all()
        
        if not lhb_details:
            print(f"❌ 未找到 {target_date} 的机构数据")
            return
        
        for lhb_detail in lhb_details:
            print(f"\n📊 {lhb_detail.stock_code} {lhb_detail.stock_name}")
            print("-" * 70)
            
            # 获取该股票的所有机构
            institutions = db.query(LhbInstitution).filter(
                LhbInstitution.lhb_detail_id == lhb_detail.id
            ).order_by(LhbInstitution.net_buy_amount.desc().nullslast()).all()
            
            if not institutions:
                print("  无机构数据")
                continue
            
            for inst in institutions:
                buy_str = f"{inst.buy_amount:,.0f}" if inst.buy_amount else "0"
                sell_str = f"{inst.sell_amount:,.0f}" if inst.sell_amount else "0"
                net_str = f"{inst.net_buy_amount:,.0f}" if inst.net_buy_amount else "0"
                net_sign = "买" if inst.net_buy_amount and inst.net_buy_amount > 0 else "卖"
                
                print(f"  {inst.institution_name:40s} | 买入: {buy_str:>15s} | 卖出: {sell_str:>15s} | 净额: {net_str:>15s} ({net_sign})")
        
    except Exception as e:
        print(f"\n❌ 显示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="同步龙虎榜个股交易机构数据")
    parser.add_argument(
        "--date",
        type=str,
        default="2025-12-31",
        help="日期，格式：YYYY-MM-DD (默认: 2025-12-31)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制处理的股票数量（用于测试）",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="仅显示机构数据，不同步",
    )
    
    args = parser.parse_args()
    
    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ 日期格式错误: {args.date}，请使用 YYYY-MM-DD 格式")
        sys.exit(1)
    
    if args.show:
        show_institutions_for_date(target_date, limit=args.limit or 10)
    else:
        success = sync_institutions_for_date(target_date, limit=args.limit)
        sys.exit(0 if success else 1)

