"""
直接检查数据库中trader_branch表的数据
执行：PYTHONPATH=. python backend/scripts/check_trader_branch_table.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal, engine
from app.models.lhb import Trader, TraderBranch
from sqlalchemy import text, func


def check_trader_branch_table():
    """直接检查trader_branch表的数据"""
    print("="*70)
    print("🔍 直接检查 trader_branch 表数据")
    print("="*70)
    
    session = SessionLocal()
    try:
        # 1. 使用原始SQL查询
        print("\n📊 使用原始SQL查询:")
        result = session.execute(text('SELECT COUNT(*) FROM trader_branch'))
        sql_count = result.scalar()
        print(f"   SQL查询结果: {sql_count} 条记录")
        
        # 2. 使用ORM查询
        orm_count = session.query(TraderBranch).count()
        print(f"   ORM查询结果: {orm_count} 条记录")
        
        # 3. 检查trader表
        trader_count = session.query(Trader).count()
        print(f"   trader表记录数: {trader_count} 条")
        
        # 4. 显示前10条记录
        print(f"\n📋 trader_branch表前10条记录:")
        branches = session.query(TraderBranch).limit(10).all()
        if branches:
            for i, branch in enumerate(branches, 1):
                trader = session.query(Trader).filter(Trader.id == branch.trader_id).first()
                trader_name = trader.name if trader else f"Unknown (id={branch.trader_id})"
                print(f"   {i:2d}. trader_id={branch.trader_id:3d} | trader={trader_name:20s} | institution={branch.institution_name[:50]}")
        else:
            print("   ⚠️  表中没有数据！")
        
        # 5. 检查每个trader的branch数量
        print(f"\n📊 每个trader的branch数量统计:")
        trader_branch_stats = session.query(
            Trader.id,
            Trader.name,
            func.count(TraderBranch.id).label('branch_count')
        ).join(
            TraderBranch, Trader.id == TraderBranch.trader_id, isouter=True
        ).group_by(Trader.id, Trader.name).order_by(
            func.count(TraderBranch.id).desc()
        ).all()
        
        traders_without_branches = [t for t in trader_branch_stats if t[2] == 0]
        traders_with_branches = [t for t in trader_branch_stats if t[2] > 0]
        
        print(f"   有branch的trader: {len(traders_with_branches)} 个")
        print(f"   没有branch的trader: {len(traders_without_branches)} 个")
        
        if traders_without_branches:
            print(f"\n   ⚠️  没有branch的trader列表:")
            for trader_id, trader_name, count in traders_without_branches[:20]:
                print(f"   - {trader_name} (id={trader_id})")
            if len(traders_without_branches) > 20:
                print(f"   ... 还有 {len(traders_without_branches) - 20} 个")
        
        # 6. 显示branch数量最多的前10个trader
        print(f"\n📈 branch数量最多的前10个trader:")
        for trader_id, trader_name, count in trader_branch_stats[:10]:
            print(f"   {trader_name:20s}: {count:3d} 个branch")
        
        # 7. 检查是否有重复的trader_id + institution_name组合
        print(f"\n🔍 检查唯一约束 (trader_id, institution_name):")
        duplicate_check = session.execute(text("""
            SELECT trader_id, institution_name, COUNT(*) as cnt
            FROM trader_branch
            GROUP BY trader_id, institution_name
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if duplicate_check:
            print(f"   ❌ 发现 {len(duplicate_check)} 个重复的 (trader_id, institution_name) 组合:")
            for trader_id, inst_name, cnt in duplicate_check[:10]:
                trader = session.query(Trader).filter(Trader.id == trader_id).first()
                trader_name = trader.name if trader else f"Unknown (id={trader_id})"
                print(f"   - {trader_name} | {inst_name}: {cnt} 次")
        else:
            print(f"   ✅ 没有发现重复的 (trader_id, institution_name) 组合")
        
        # 8. 使用完全独立的连接再次检查
        print(f"\n🔄 使用完全独立的连接检查:")
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        independent_engine = create_engine(str(engine.url), pool_pre_ping=True)
        IndependentSession = sessionmaker(bind=independent_engine)
        ind_session = IndependentSession()
        try:
            ind_count = ind_session.execute(text('SELECT COUNT(*) FROM trader_branch')).scalar()
            print(f"   独立连接SQL查询: {ind_count} 条记录")
            
            ind_orm_count = ind_session.query(TraderBranch).count()
            print(f"   独立连接ORM查询: {ind_orm_count} 条记录")
            
            if ind_count == 0:
                print(f"   ⚠️  警告: 独立连接查询显示表中没有数据！")
        finally:
            ind_session.close()
            independent_engine.dispose()
        
        # 9. 总结
        print(f"\n" + "="*70)
        print("📋 检查结果总结")
        print("="*70)
        
        if sql_count == 0 and orm_count == 0:
            print("\n❌ 问题确认: trader_branch表中确实没有数据！")
            print("\n可能的原因:")
            print("1. 导入脚本执行失败")
            print("2. 事务未提交")
            print("3. 连接到了错误的数据库")
            print("4. 表结构存在问题")
            
            print("\n建议操作:")
            print("1. 重新运行导入脚本:")
            print("   PYTHONPATH=. python backend/scripts/import_traders_from_file.py backend/data/traders_data.txt --force")
            print("2. 检查数据库连接配置")
            print("3. 检查表结构是否正确")
        elif sql_count != orm_count:
            print(f"\n⚠️  警告: SQL查询 ({sql_count}) 和 ORM查询 ({orm_count}) 结果不一致！")
        else:
            print(f"\n✅ trader_branch表中有 {sql_count} 条记录")
            if len(traders_without_branches) > 0:
                print(f"⚠️  但有 {len(traders_without_branches)} 个trader没有关联branch")
            else:
                print("✅ 所有trader都有关联branch")
        
    except Exception as e:
        print(f"\n❌ 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    check_trader_branch_table()
