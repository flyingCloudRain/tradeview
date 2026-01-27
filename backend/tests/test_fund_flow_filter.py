"""
测试资金流筛选功能
"""
import sys
import os
from datetime import date

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.session import SessionLocal
from app.services.fund_flow_service import FundFlowService
from app.schemas.fund_flow import FundFlowFilterRequest, DateRangeCondition, DateRange, NetInflowRange


def test_filter_fund_flow():
    """测试资金流筛选功能"""
    print("=" * 60)
    print("测试资金流筛选功能")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 构建筛选条件
        # 条件1: 1月10-14日，主力净流入>1亿
        condition1 = DateRangeCondition(
            date_range=DateRange(
                start=date(2026, 1, 10),
                end=date(2026, 1, 14)
            ),
            main_net_inflow=NetInflowRange(
                min=100000000  # 1亿
            )
        )
        
        # 条件2: 1月09-14日，主力净流入<1000万
        condition2 = DateRangeCondition(
            date_range=DateRange(
                start=date(2026, 1, 9),
                end=date(2026, 1, 14)
            ),
            main_net_inflow=NetInflowRange(
                max=10000000  # 1000万
            )
        )
        
        # 创建请求
        request = FundFlowFilterRequest(
            conditions=[condition1, condition2],
            page=1,
            page_size=20
        )
        
        print(f"\n筛选条件:")
        print(f"  条件1: {condition1.date_range.start} 至 {condition1.date_range.end}, 主力净流入 >= {condition1.main_net_inflow.min}")
        print(f"  条件2: {condition2.date_range.start} 至 {condition2.date_range.end}, 主力净流入 <= {condition2.main_net_inflow.max}")
        print()
        
        # 执行筛选
        print("开始筛选...")
        items, total = FundFlowService.filter_fund_flow_by_conditions(
            db=db,
            conditions=request.conditions,
            concept_ids=request.concept_ids,
            concept_names=request.concept_names,
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by,
            order=request.order
        )
        
        print(f"\n✅ 筛选完成!")
        print(f"  找到 {total} 只股票满足所有条件")
        print(f"  当前页: {len(items)} 条记录")
        print()
        
        if items:
            print("前5条结果:")
            for idx, item in enumerate(items[:5], 1):
                print(f"\n  {idx}. {item['stock_name']} ({item['stock_code']})")
                print(f"     最新日期: {item['latest_date']}")
                print(f"     最新主力净流入: {item['latest_main_net_inflow']:,.0f} 元" if item['latest_main_net_inflow'] else "     最新主力净流入: 无数据")
                print(f"     匹配条件数: {len(item['match_conditions'])}")
                if item['concepts']:
                    concept_names = [c['name'] for c in item['concepts']]
                    print(f"     概念板块: {', '.join(concept_names[:3])}")
        else:
            print("⚠️  没有找到满足条件的股票")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_simple_filter():
    """测试简单筛选（单个条件）"""
    print("\n" + "=" * 60)
    print("测试简单筛选（单个条件）")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 单个条件：1月10-14日，主力净流入>5000万
        condition = DateRangeCondition(
            date_range=DateRange(
                start=date(2026, 1, 10),
                end=date(2026, 1, 14)
            ),
            main_net_inflow=NetInflowRange(
                min=50000000  # 5000万
            )
        )
        
        print(f"\n筛选条件:")
        print(f"  日期范围: {condition.date_range.start} 至 {condition.date_range.end}")
        print(f"  主力净流入 >= {condition.main_net_inflow.min:,.0f} 元")
        print()
        
        items, total = FundFlowService.filter_fund_flow_by_conditions(
            db=db,
            conditions=[condition],
            page=1,
            page_size=10
        )
        
        print(f"✅ 找到 {total} 只股票")
        if items:
            print(f"\n前3条结果:")
            for idx, item in enumerate(items[:3], 1):
                print(f"  {idx}. {item['stock_name']} ({item['stock_code']}) - 主力净流入: {item['latest_main_net_inflow']:,.0f} 元" if item['latest_main_net_inflow'] else f"  {idx}. {item['stock_name']} ({item['stock_code']}) - 主力净流入: 无数据")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("资金流筛选功能测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("简单筛选", test_simple_filter()))
    results.append(("复杂筛选（多条件）", test_filter_fund_flow()))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
