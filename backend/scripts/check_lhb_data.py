#!/usr/bin/env python3
"""
检查龙虎榜数据
"""
import sys
import os
from pathlib import Path
from datetime import date

# 添加项目根目录到路径
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from app.database.session import SessionLocal
from app.models.lhb import LhbDetail, LhbInstitution
from sqlalchemy import func

def check_lhb_data():
    """检查龙虎榜数据"""
    db = SessionLocal()
    try:
        print("=" * 70)
        print("检查龙虎榜数据")
        print("=" * 70)
        
        # 检查数据库连接
        from app.config import settings
        db_url = settings.DATABASE_URL
        # 隐藏密码
        if '@' in db_url:
            parts = db_url.split('@')
            if len(parts) == 2:
                db_url_display = f"{parts[0].split('://')[0]}://***@{parts[1]}"
            else:
                db_url_display = db_url
        else:
            db_url_display = db_url
        print(f"数据库: {db_url_display}")
        print()
        
        # 检查 lhb_detail 表
        total_detail = db.query(LhbDetail).count()
        print(f"📊 lhb_detail 表总记录数: {total_detail}")
        
        if total_detail > 0:
            # 获取日期范围
            min_date = db.query(func.min(LhbDetail.date)).scalar()
            max_date = db.query(func.max(LhbDetail.date)).scalar()
            print(f"📅 日期范围: {min_date} 到 {max_date}")
            
            # 检查2026-01-09的数据
            target_date = date(2026, 1, 9)
            count_2026_01_09 = db.query(LhbDetail).filter(LhbDetail.date == target_date).count()
            print(f"📅 2026-01-09 的数据: {count_2026_01_09} 条")
            
            # 显示最近的几个日期
            recent_dates = db.query(LhbDetail.date).distinct().order_by(LhbDetail.date.desc()).limit(5).all()
            print(f"\n📅 最近的日期（前5个）:")
            for d in recent_dates:
                count = db.query(LhbDetail).filter(LhbDetail.date == d[0]).count()
                print(f"   {d[0]}: {count} 条")
            
            # 显示2026-01-09的示例数据
            if count_2026_01_09 > 0:
                samples = db.query(LhbDetail).filter(LhbDetail.date == target_date).limit(3).all()
                print(f"\n📋 2026-01-09 示例数据（前3条）:")
                for s in samples:
                    print(f"   {s.stock_code} {s.stock_name} - 净买额: {s.net_buy_amount}")
        else:
            print("⚠️  lhb_detail 表中没有数据")
        
        print()
        
        # 检查 lhb_institution 表
        total_institution = db.query(LhbInstitution).count()
        print(f"📊 lhb_institution 表总记录数: {total_institution}")
        
        if total_institution > 0:
            # 获取日期范围
            min_date = db.query(func.min(LhbInstitution.date)).scalar()
            max_date = db.query(func.max(LhbInstitution.date)).scalar()
            print(f"📅 日期范围: {min_date} 到 {max_date}")
            
            # 检查2026-01-09的数据
            target_date = date(2026, 1, 9)
            count_2026_01_09 = db.query(LhbInstitution).filter(LhbInstitution.date == target_date).count()
            print(f"📅 2026-01-09 的数据: {count_2026_01_09} 条")
        
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_lhb_data()
