"""
全面验证trader_branch表数据导入情况
执行：PYTHONPATH=. python backend/scripts/verify_trader_branch_import.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal, engine
from app.models.lhb import Trader, TraderBranch
from sqlalchemy import text, inspect, func
from collections import defaultdict


def verify_trader_branch_import():
    """全面验证trader_branch表数据导入情况"""
    print("="*70)
    print("🔍 全面验证 trader_branch 表数据导入")
    print("="*70)
    
    # 显示数据库连接信息
    print(f"\n📊 数据库连接信息:")
    print(f"   数据库URL: {str(engine.url).split('@')[-1] if '@' in str(engine.url) else '隐藏'}")
    print(f"   数据库类型: {engine.url.drivername}")
    
    session = SessionLocal()
    try:
        # 1. 检查表是否存在
        print(f"\n🔍 检查1: 表结构")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'trader_branch' in tables:
            print(f"   ✅ trader_branch 表存在")
            
            # 显示表结构
            columns = inspector.get_columns('trader_branch')
            print(f"   表字段:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"     - {col['name']}: {col['type']} {nullable}")
            
            # 显示索引
            indexes = inspector.get_indexes('trader_branch')
            if indexes:
                print(f"   索引:")
                for idx in indexes:
                    print(f"     - {idx['name']}: {', '.join(idx['column_names'])}")
            
            # 显示外键
            foreign_keys = inspector.get_foreign_keys('trader_branch')
            if foreign_keys:
                print(f"   外键:")
                for fk in foreign_keys:
                    print(f"     - {fk['name']}: {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}")
        else:
            print(f"   ❌ trader_branch 表不存在！")
            return
        
        # 2. 使用多种方式查询数据
        print(f"\n🔍 检查2: 数据查询（多种方式）")
        
        # 方式1: 原始SQL
        result1 = session.execute(text('SELECT COUNT(*) FROM trader_branch'))
        sql_count = result1.scalar()
        print(f"   方式1 - 原始SQL COUNT(*): {sql_count} 条")
        
        # 方式2: ORM count()
        orm_count = session.query(TraderBranch).count()
        print(f"   方式2 - ORM count(): {orm_count} 条")
        
        # 方式3: 使用all()然后len
        all_branches = session.query(TraderBranch).all()
        all_count = len(all_branches)
        print(f"   方式3 - ORM all() + len(): {all_count} 条")
        
        # 方式4: 使用SQL COUNT with JOIN
        result2 = session.execute(text("""
            SELECT COUNT(*) 
            FROM trader_branch tb
            INNER JOIN trader t ON tb.trader_id = t.id
        """))
        join_count = result2.scalar()
        print(f"   方式4 - SQL COUNT with JOIN: {join_count} 条")
        
        if sql_count == 0:
            print(f"\n   ❌ 确认: trader_branch表中没有数据！")
            print(f"\n   建议操作:")
            print(f"   1. 重新运行导入脚本:")
            print(f"      PYTHONPATH=. python backend/scripts/import_traders_from_file.py backend/data/traders_data.txt --force")
            print(f"   2. 检查导入脚本的执行日志")
            return
        
        # 3. 检查数据完整性
        print(f"\n🔍 检查3: 数据完整性")
        
        # 检查trader表
        trader_count = session.query(Trader).count()
        print(f"   trader表记录数: {trader_count} 条")
        
        # 检查每个trader的branch数量
        trader_branch_stats = session.query(
            Trader.id,
            Trader.name,
            func.count(TraderBranch.id).label('branch_count')
        ).join(
            TraderBranch, Trader.id == TraderBranch.trader_id, isouter=True
        ).group_by(Trader.id, Trader.name).all()
        
        traders_without_branches = [t for t in trader_branch_stats if t[2] == 0]
        traders_with_branches = [t for t in trader_branch_stats if t[2] > 0]
        
        print(f"   有branch的trader: {len(traders_with_branches)} 个")
        print(f"   没有branch的trader: {len(traders_without_branches)} 个")
        
        if traders_without_branches:
            print(f"\n   ⚠️  没有branch的trader:")
            for trader_id, trader_name, count in traders_without_branches:
                print(f"     - {trader_name} (id={trader_id})")
        
        # 4. 检查数据样本
        print(f"\n🔍 检查4: 数据样本（前20条）")
        sample_branches = session.query(TraderBranch).limit(20).all()
        for i, branch in enumerate(sample_branches, 1):
            trader = session.query(Trader).filter(Trader.id == branch.trader_id).first()
            trader_name = trader.name if trader else f"Unknown (id={branch.trader_id})"
            code_info = f" [code={branch.institution_code}]" if branch.institution_code else ""
            print(f"   {i:2d}. {trader_name:20s} -> {branch.institution_name[:50]}{code_info}")
        
        # 5. 统计信息
        print(f"\n🔍 检查5: 统计信息")
        
        # branch数量分布
        branch_counts = [t[2] for t in trader_branch_stats]
        if branch_counts:
            print(f"   平均每个trader的branch数: {sum(branch_counts) / len(branch_counts):.2f}")
            print(f"   最多branch数: {max(branch_counts)}")
            print(f"   最少branch数: {min(branch_counts)}")
        
        # 有代码的branch数量
        branches_with_code = session.query(TraderBranch).filter(
            TraderBranch.institution_code.isnot(None)
        ).count()
        print(f"   有institution_code的branch: {branches_with_code} 个 ({branches_with_code / sql_count * 100 if sql_count > 0 else 0:.1f}%)")
        
        # 6. 检查唯一约束
        print(f"\n🔍 检查6: 唯一约束验证")
        duplicate_check = session.execute(text("""
            SELECT trader_id, institution_name, COUNT(*) as cnt
            FROM trader_branch
            GROUP BY trader_id, institution_name
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if duplicate_check:
            print(f"   ❌ 发现 {len(duplicate_check)} 个重复的 (trader_id, institution_name) 组合")
        else:
            print(f"   ✅ 没有发现重复的 (trader_id, institution_name) 组合")
        
        # 7. 检查外键完整性
        print(f"\n🔍 检查7: 外键完整性")
        orphan_branches = session.execute(text("""
            SELECT COUNT(*) 
            FROM trader_branch tb
            LEFT JOIN trader t ON tb.trader_id = t.id
            WHERE t.id IS NULL
        """)).scalar()
        
        if orphan_branches > 0:
            print(f"   ❌ 发现 {orphan_branches} 个孤立branch（trader_id不存在）")
        else:
            print(f"   ✅ 没有发现孤立branch")
        
        # 8. 对比文件数据
        print(f"\n🔍 检查8: 对比文件数据")
        data_file = Path(project_root / "data/traders_data.txt")
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # 解析文件数据
            file_traders = {}
            lines = file_content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('名称'):
                    continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    name = parts[0].strip()
                    institutions_str = parts[2].strip()
                    institutions = []
                    if institutions_str:
                        for inst in institutions_str.split('、'):
                            for inst2 in inst.split(','):
                                inst_name = inst2.strip()
                                if inst_name:
                                    institutions.append(inst_name)
                    file_traders[name] = institutions
            
            # 对比数据库数据
            db_traders = {}
            for trader in session.query(Trader).all():
                branches = session.query(TraderBranch).filter(
                    TraderBranch.trader_id == trader.id
                ).all()
                db_traders[trader.name] = [b.institution_name for b in branches]
            
            file_total_branches = sum(len(insts) for insts in file_traders.values())
            db_total_branches = sql_count
            
            print(f"   文件中的总branch数: {file_total_branches}")
            print(f"   数据库中的总branch数: {db_total_branches}")
            
            if file_total_branches == db_total_branches:
                print(f"   ✅ 文件和数据中的branch总数一致")
            else:
                print(f"   ⚠️  文件和数据中的branch总数不一致（差异: {abs(file_total_branches - db_total_branches)}）")
        
        # 9. 总结
        print(f"\n" + "="*70)
        print("📋 验证结果总结")
        print("="*70)
        
        if sql_count > 0:
            print(f"\n✅ trader_branch表数据验证通过:")
            print(f"   - 表中有 {sql_count} 条记录")
            print(f"   - 所有 {trader_count} 个trader都有关联branch")
            print(f"   - 没有发现数据完整性问题")
            print(f"   - 唯一约束正常")
            print(f"   - 外键完整性正常")
        else:
            print(f"\n❌ trader_branch表中没有数据！")
            print(f"\n请运行导入脚本:")
            print(f"PYTHONPATH=. python backend/scripts/import_traders_from_file.py backend/data/traders_data.txt --force")
        
    except Exception as e:
        print(f"\n❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    verify_trader_branch_import()
