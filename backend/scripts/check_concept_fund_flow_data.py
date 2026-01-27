#!/usr/bin/env python3
"""
概念资金流数据检查脚本
检查数据库中概念资金流数据的情况，诊断数据不显示的问题
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.session import SessionLocal
from app.models.fund_flow import ConceptFundFlow
from app.utils.date_utils import get_trading_date


def check_concept_fund_flow_data():
    """检查概念资金流数据"""
    db: Session = SessionLocal()
    
    try:
        print("=" * 80)
        print("概念资金流数据检查")
        print("=" * 80)
        
        # 1. 检查数据库中的总记录数
        total_count = db.query(func.count(ConceptFundFlow.id)).scalar()
        print(f"\n1. 数据库总记录数: {total_count}")
        
        if total_count == 0:
            print("   ⚠️  警告: 数据库中没有概念资金流数据！")
            print("   建议: 运行数据同步任务 sync_concept_fund_flow")
            return
        
        # 2. 检查日期范围
        date_range = db.query(
            func.min(ConceptFundFlow.date).label('min_date'),
            func.max(ConceptFundFlow.date).label('max_date')
        ).first()
        
        if date_range and date_range.min_date:
            print(f"\n2. 数据日期范围:")
            print(f"   最早日期: {date_range.min_date}")
            print(f"   最新日期: {date_range.max_date}")
            
            # 计算日期差
            days_diff = (date_range.max_date - date_range.min_date).days
            print(f"   日期跨度: {days_diff} 天")
        else:
            print("\n2. 数据日期范围: 无数据")
            return
        
        # 3. 检查最近几天的数据
        print(f"\n3. 最近7天的数据统计:")
        today = date.today()
        for i in range(7):
            check_date = today - timedelta(days=i)
            count = db.query(func.count(ConceptFundFlow.id)).filter(
                ConceptFundFlow.date == check_date
            ).scalar()
            
            status = "✓" if count > 0 else "✗"
            print(f"   {status} {check_date}: {count} 条记录")
        
        # 4. 检查最新交易日的数据
        latest_trading_date = get_trading_date()
        if latest_trading_date:
            latest_count = db.query(func.count(ConceptFundFlow.id)).filter(
                ConceptFundFlow.date == latest_trading_date
            ).scalar()
            print(f"\n4. 最新交易日 ({latest_trading_date}) 数据:")
            print(f"   记录数: {latest_count}")
            
            if latest_count > 0:
                # 显示前10条数据
                latest_data = db.query(ConceptFundFlow).filter(
                    ConceptFundFlow.date == latest_trading_date
                ).order_by(desc(ConceptFundFlow.net_amount)).limit(10).all()
                
                print(f"\n   前10条数据（按净额排序）:")
                print(f"   {'日期':<12} {'概念':<30} {'净额(亿)':<15} {'流入(亿)':<15} {'流出(亿)':<15}")
                print("   " + "-" * 87)
                for item in latest_data:
                    net_amount_yi = (item.net_amount / 100000000) if item.net_amount else 0
                    inflow_yi = (item.inflow / 100000000) if item.inflow else 0
                    outflow_yi = (item.outflow / 100000000) if item.outflow else 0
                    print(f"   {str(item.date):<12} {item.concept[:28]:<30} {net_amount_yi:>12.2f} {inflow_yi:>12.2f} {outflow_yi:>12.2f}")
            else:
                print("   ⚠️  警告: 最新交易日没有数据！")
        else:
            print("\n4. 无法获取最新交易日")
        
        # 5. 检查数据完整性
        print(f"\n5. 数据完整性检查:")
        
        # 检查空值
        null_concept = db.query(func.count(ConceptFundFlow.id)).filter(
            ConceptFundFlow.concept.is_(None)
        ).scalar()
        null_net_amount = db.query(func.count(ConceptFundFlow.id)).filter(
            ConceptFundFlow.net_amount.is_(None)
        ).scalar()
        null_date = db.query(func.count(ConceptFundFlow.id)).filter(
            ConceptFundFlow.date.is_(None)
        ).scalar()
        
        print(f"   概念为空: {null_concept} 条")
        print(f"   净额为NULL: {null_net_amount} 条")
        print(f"   日期为NULL: {null_date} 条")
        
        # 6. 检查每个日期的记录数分布
        print(f"\n6. 各日期记录数统计（最近10个有数据的日期）:")
        date_counts = db.query(
            ConceptFundFlow.date,
            func.count(ConceptFundFlow.id).label('count')
        ).group_by(ConceptFundFlow.date).order_by(
            desc(ConceptFundFlow.date)
        ).limit(10).all()
        
        if date_counts:
            print(f"   {'日期':<12} {'记录数':<10} {'状态'}")
            print("   " + "-" * 35)
            for date_item, count in date_counts:
                status = "正常" if count >= 50 else "偏少" if count > 0 else "异常"
                print(f"   {str(date_item):<12} {count:<10} {status}")
        else:
            print("   无数据")
        
        # 7. 检查概念数量
        concept_count = db.query(func.count(func.distinct(ConceptFundFlow.concept))).scalar()
        print(f"\n7. 唯一概念数量: {concept_count}")
        
        # 8. 检查API查询逻辑
        print(f"\n8. API查询逻辑检查:")
        print("   单日期查询: GET /stock-fund-flow/concept?date=YYYY-MM-DD")
        print("   日期范围查询: GET /stock-fund-flow/concept?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD")
        print("   如果date为空且没有日期范围，会查询最新交易日的数据")
        
        # 9. 建议
        print(f"\n9. 诊断建议:")
        if total_count == 0:
            print("   - 数据库中没有数据，需要运行数据同步任务")
            print("   - 可以手动调用: FundFlowService.sync_concept_fund_flow(db, target_date)")
        elif latest_count == 0:
            print("   - 最新交易日没有数据，可能需要同步最新数据")
            print("   - 检查调度器是否正常运行")
            print("   - 检查数据源接口是否可用")
        else:
            print("   - 数据存在，检查前端API调用和数据处理逻辑")
            print("   - 检查浏览器控制台是否有错误信息")
            print("   - 检查网络请求是否成功返回数据")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"\n❌ 检查过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_concept_fund_flow_data()
