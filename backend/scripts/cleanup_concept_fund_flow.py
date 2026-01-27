"""
清理概念资金流数据库中的历史数据

删除指定日期之前的概念资金流数据。

执行方式：
    poetry run python backend/scripts/cleanup_concept_fund_flow.py
或：
    python backend/scripts/cleanup_concept_fund_flow.py

默认删除2025-01-15之前的数据，可以通过命令行参数指定日期：
    python backend/scripts/cleanup_concept_fund_flow.py --before-date 2025-01-15
"""
import sys
from pathlib import Path
from datetime import date, datetime
from sqlalchemy import func, and_

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.models.fund_flow import ConceptFundFlow


def cleanup_concept_fund_flow(before_date: date, confirm: bool = False) -> int:
    """
    清理概念资金流表中指定日期之前的数据
    
    Args:
        before_date: 删除此日期之前的所有数据（不包含此日期）
        confirm: 是否已确认删除操作
    
    Returns:
        删除的记录数
    """
    session = SessionLocal()
    try:
        # 先统计要删除的记录数
        count_query = session.query(func.count(ConceptFundFlow.id)).filter(
            ConceptFundFlow.date < before_date
        )
        total_count = count_query.scalar()
        
        if total_count == 0:
            print(f"✅ 概念资金流表中没有 {before_date} 之前的数据，无需清理")
            return 0
        
        # 显示统计信息
        date_range_query = session.query(
            func.min(ConceptFundFlow.date).label('min_date'),
            func.max(ConceptFundFlow.date).label('max_date')
        ).filter(ConceptFundFlow.date < before_date)
        date_range = date_range_query.first()
        
        print(f"📊 统计信息:")
        print(f"   删除日期范围: {date_range.min_date} 至 {before_date} (不包含)")
        print(f"   将删除记录数: {total_count}")
        
        if not confirm:
            print(f"\n⚠️  警告：此操作将删除概念资金流表中 {before_date} 之前的所有 {total_count} 条记录！")
            print("⚠️  此操作不可逆，请谨慎操作！")
            response = input("请输入 'YES' 确认删除，或按 Enter 取消: ").strip()
            
            if response != 'YES':
                print("❌ 操作已取消")
                return 0
        
        # 执行删除
        print(f"\n🔄 开始删除数据...")
        deleted_count = session.query(ConceptFundFlow).filter(
            ConceptFundFlow.date < before_date
        ).delete(synchronize_session=False)
        
        session.commit()
        
        print(f"✅ 成功删除 {deleted_count} 条概念资金流记录")
        return deleted_count
        
    except Exception as e:
        session.rollback()
        print(f"❌ 清理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def main():
    """主函数"""
    # 解析命令行参数
    before_date_str = None
    if '--before-date' in sys.argv:
        idx = sys.argv.index('--before-date')
        if idx + 1 < len(sys.argv):
            before_date_str = sys.argv[idx + 1]
        else:
            print("❌ 错误: --before-date 参数需要指定日期")
            sys.exit(1)
    
    # 默认日期：2025-01-15
    if not before_date_str:
        before_date = date(2025, 1, 15)
    else:
        try:
            before_date = datetime.strptime(before_date_str, '%Y-%m-%d').date()
        except ValueError:
            print(f"❌ 错误: 日期格式不正确，请使用 YYYY-MM-DD 格式，例如: 2025-01-15")
            sys.exit(1)
    
    # 检查是否需要确认（可以通过命令行参数跳过确认）
    confirm = '--yes' in sys.argv or '-y' in sys.argv
    
    print("=" * 60)
    print("清理概念资金流历史数据")
    print("=" * 60)
    print(f"删除日期: {before_date} 之前的所有数据")
    print()
    
    try:
        deleted_count = cleanup_concept_fund_flow(before_date, confirm=confirm)
        
        if deleted_count > 0:
            print("\n" + "=" * 60)
            print("清理完成")
            print("=" * 60)
            print(f"已删除 {deleted_count} 条概念资金流记录")
        else:
            print("\n无需清理数据")
            
    except Exception as e:
        print(f"\n❌ 执行失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
