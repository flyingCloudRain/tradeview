"""
检查概念资金流数据库中的日期范围

执行方式：
    python backend/scripts/check_concept_fund_flow_dates.py
"""
import sys
from pathlib import Path
from sqlalchemy import func

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.models.fund_flow import ConceptFundFlow


def check_dates():
    """检查概念资金流表中的日期范围"""
    session = SessionLocal()
    try:
        # 统计总记录数
        total_count = session.query(func.count(ConceptFundFlow.id)).scalar()
        
        if total_count == 0:
            print("✅ 概念资金流表为空，没有数据")
            return
        
        # 查询日期范围
        date_range = session.query(
            func.min(ConceptFundFlow.date).label('min_date'),
            func.max(ConceptFundFlow.date).label('max_date'),
            func.count(func.distinct(ConceptFundFlow.date)).label('date_count')
        ).first()
        
        print("=" * 60)
        print("概念资金流数据统计")
        print("=" * 60)
        print(f"总记录数: {total_count}")
        print(f"最早日期: {date_range.min_date}")
        print(f"最晚日期: {date_range.max_date}")
        print(f"日期数量: {date_range.date_count}")
        
        # 查询每个日期的记录数
        print("\n各日期记录数统计（前20个日期）:")
        date_counts = session.query(
            ConceptFundFlow.date,
            func.count(ConceptFundFlow.id).label('count')
        ).group_by(ConceptFundFlow.date).order_by(ConceptFundFlow.date.desc()).limit(20).all()
        
        for dt, count in date_counts:
            print(f"  {dt}: {count} 条")
        
        # 检查2025-01-15之前的数据
        from datetime import date
        cutoff_date = date(2025, 1, 15)
        before_count = session.query(func.count(ConceptFundFlow.id)).filter(
            ConceptFundFlow.date < cutoff_date
        ).scalar()
        
        print(f"\n{cutoff_date} 之前的记录数: {before_count}")
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    check_dates()
