"""
修复龙虎榜机构数据的flag字段
重新同步数据，使用flag字段区分买入和卖出
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
from sqlalchemy import and_, func
import akshare as ak


def fix_institutions_flag(target_date: date, limit: int = None):
    """修复指定日期的机构数据flag字段"""
    print("=" * 70)
    print(f"修复 {target_date} 龙虎榜机构数据的flag字段")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        # 获取该日期的所有龙虎榜股票
        lhb_details = db.query(LhbDetail).filter(LhbDetail.date == target_date).all()
        
        if not lhb_details:
            print(f"❌ 未找到 {target_date} 的龙虎榜基础数据")
            return False
        
        print(f"\n📋 共 {len(lhb_details)} 只股票需要修复\n")
        
        # 限制处理数量（用于测试）
        if limit:
            lhb_details = lhb_details[:limit]
            print(f"⚠️  限制处理前 {limit} 只股票\n")
        
        date_str = target_date.strftime("%Y%m%d")
        success_count = 0
        fail_count = 0
        total_institutions = 0
        
        for i, lhb_detail in enumerate(lhb_details, 1):
            stock_code = lhb_detail.stock_code
            stock_name = lhb_detail.stock_name
            
            print(f"[{i}/{len(lhb_details)}] {stock_code} {stock_name} - ", end="", flush=True)
            
            try:
                # 删除该股票的所有机构数据
                deleted_count = db.query(LhbInstitution).filter(
                    LhbInstitution.lhb_detail_id == lhb_detail.id
                ).delete()
                
                if deleted_count > 0:
                    print(f"删除旧数据 {deleted_count} 条, ", end="", flush=True)
                
                # 重新获取买入机构
                df_buy = safe_akshare_call(
                    ak.stock_lhb_stock_detail_em,
                    symbol=stock_code,
                    date=date_str,
                    flag='买入'
                )
                
                # 重新获取卖出机构
                df_sell = safe_akshare_call(
                    ak.stock_lhb_stock_detail_em,
                    symbol=stock_code,
                    date=date_str,
                    flag='卖出'
                )
                
                if df_buy is None and df_sell is None:
                    print("❌ 未获取到机构数据")
                    fail_count += 1
                    db.rollback()
                    continue
                
                # 重新保存机构数据（会使用flag字段）
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
                    time.sleep(0.3)
                    
            except Exception as e:
                print(f"❌ 错误: {str(e)[:50]}")
                fail_count += 1
                db.rollback()
                continue
        
        # 输出统计结果
        print()
        print("=" * 70)
        print("📊 修复结果统计")
        print("=" * 70)
        print(f"✅ 成功: {success_count} 只股票")
        print(f"❌ 失败: {fail_count} 只股票")
        print(f"📈 总机构记录数: {total_institutions} 条")
        print("=" * 70)
        
        return success_count > 0
        
    except Exception as e:
        print(f"\n❌ 修复过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def verify_flag_data(target_date: date):
    """验证flag字段数据"""
    print("=" * 70)
    print(f"验证 {target_date} 的flag字段数据")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        # 统计flag分布
        flag_stats = db.query(
            LhbInstitution.flag,
            func.count(LhbInstitution.id).label('count')
        ).filter(
            LhbInstitution.date == target_date
        ).group_by(LhbInstitution.flag).all()
        
        print("\nFlag分布:")
        for flag, count in flag_stats:
            print(f"  {flag}: {count} 条")
        
        # 检查是否有空flag
        null_count = db.query(LhbInstitution).filter(
            and_(
                LhbInstitution.date == target_date,
                LhbInstitution.flag.is_(None)
            )
        ).count()
        
        if null_count > 0:
            print(f"\n⚠️  发现 {null_count} 条记录的flag为空")
        else:
            print("\n✅ 所有记录的flag字段都已设置")
        
        # 显示示例数据
        print("\n示例数据（前5条）:")
        samples = db.query(LhbInstitution).filter(
            LhbInstitution.date == target_date
        ).limit(5).all()
        
        for inst in samples:
            lhb = db.query(LhbDetail).filter(LhbDetail.id == inst.lhb_detail_id).first()
            stock_name = lhb.stock_name if lhb else "未知"
            print(f"  {inst.stock_code} {stock_name} | {inst.institution_name} | flag={inst.flag} | 净额={inst.net_buy_amount}")
        
    except Exception as e:
        print(f"\n❌ 验证过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="修复龙虎榜机构数据的flag字段")
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
        "--verify",
        action="store_true",
        help="仅验证flag字段数据，不修复",
    )
    
    args = parser.parse_args()
    
    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print(f"❌ 日期格式错误: {args.date}，请使用 YYYY-MM-DD 格式")
        sys.exit(1)
    
    if args.verify:
        verify_flag_data(target_date)
    else:
        success = fix_institutions_flag(target_date, limit=args.limit)
        if success:
            print("\n开始验证修复结果...")
            verify_flag_data(target_date)
        sys.exit(0 if success else 1)

