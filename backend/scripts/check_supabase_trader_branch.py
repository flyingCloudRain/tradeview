"""
检查Supabase数据库中trader_branch表的数据
执行：PYTHONPATH=. python backend/scripts/check_supabase_trader_branch.py
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal, engine
from app.models.lhb import Trader, TraderBranch
from app.config import settings
from sqlalchemy import text, inspect, func


def check_supabase_trader_branch():
    """检查Supabase数据库中trader_branch表的数据"""
    print("="*70)
    print("🔍 检查 Supabase 数据库中 trader_branch 表数据")
    print("="*70)
    
    # 显示数据库连接信息
    print(f"\n📊 数据库连接信息:")
    db_url = str(engine.url)
    # 隐藏密码
    if '@' in db_url:
        parts = db_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                db_url_display = db_url.replace(user_pass, f"{user}:***")
            else:
                db_url_display = db_url
        else:
            db_url_display = db_url
        print(f"   数据库URL: {db_url_display.split('@')[-1]}")
    else:
        print(f"   数据库URL: {db_url}")
    
    print(f"   数据库类型: {engine.url.drivername}")
    
    # 检查是否是Supabase
    is_supabase = 'supabase' in db_url.lower() or 'postgresql' in engine.url.drivername
    if is_supabase:
        print(f"   ✅ 检测到 Supabase/PostgreSQL 数据库")
    else:
        print(f"   ⚠️  当前连接的不是 Supabase 数据库")
        print(f"   请设置 DATABASE_URL 环境变量指向 Supabase")
    
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
                print(f"     - {col['name']}: {str(col['type'])} {nullable}")
        else:
            print(f"   ❌ trader_branch 表不存在！")
            print(f"   请先运行数据库迁移:")
            print(f"   cd backend && alembic upgrade head")
            return
        
        # 2. 使用多种方式查询数据
        print(f"\n🔍 检查2: 数据查询（多种方式）")
        
        # 方式1: 原始SQL
        try:
            result1 = session.execute(text('SELECT COUNT(*) FROM trader_branch'))
            sql_count = result1.scalar()
            print(f"   方式1 - 原始SQL COUNT(*): {sql_count} 条")
        except Exception as e:
            print(f"   方式1 - 原始SQL COUNT(*) 失败: {str(e)}")
            sql_count = 0
        
        # 方式2: ORM count()
        try:
            orm_count = session.query(TraderBranch).count()
            print(f"   方式2 - ORM count(): {orm_count} 条")
        except Exception as e:
            print(f"   方式2 - ORM count() 失败: {str(e)}")
            orm_count = 0
        
        # 方式3: 使用SQL COUNT with JOIN
        try:
            result2 = session.execute(text("""
                SELECT COUNT(*) 
                FROM trader_branch tb
                INNER JOIN trader t ON tb.trader_id = t.id
            """))
            join_count = result2.scalar()
            print(f"   方式3 - SQL COUNT with JOIN: {join_count} 条")
        except Exception as e:
            print(f"   方式3 - SQL COUNT with JOIN 失败: {str(e)}")
            join_count = 0
        
        if sql_count == 0:
            print(f"\n   ❌ 确认: trader_branch表中没有数据！")
            print(f"\n   建议操作:")
            print(f"   1. 检查是否已运行导入脚本:")
            print(f"      PYTHONPATH=. python backend/scripts/import_traders_from_file.py backend/data/traders_data.txt --force")
            print(f"   2. 确认 DATABASE_URL 环境变量指向正确的 Supabase 数据库")
            print(f"   3. 检查数据库连接是否正常")
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
            for trader_id, trader_name, count in traders_without_branches[:20]:
                print(f"     - {trader_name} (id={trader_id})")
            if len(traders_without_branches) > 20:
                print(f"     ... 还有 {len(traders_without_branches) - 20} 个")
        
        # 4. 检查数据样本
        print(f"\n🔍 检查4: 数据样本（前20条）")
        try:
            sample_branches = session.query(TraderBranch).limit(20).all()
            for i, branch in enumerate(sample_branches, 1):
                trader = session.query(Trader).filter(Trader.id == branch.trader_id).first()
                trader_name = trader.name if trader else f"Unknown (id={branch.trader_id})"
                code_info = f" [code={branch.institution_code}]" if branch.institution_code else ""
                print(f"   {i:2d}. {trader_name:20s} -> {branch.institution_name[:50]}{code_info}")
        except Exception as e:
            print(f"   ❌ 查询数据样本失败: {str(e)}")
        
        # 5. 统计信息
        print(f"\n🔍 检查5: 统计信息")
        
        # branch数量分布
        branch_counts = [t[2] for t in trader_branch_stats]
        if branch_counts:
            print(f"   平均每个trader的branch数: {sum(branch_counts) / len(branch_counts):.2f}")
            print(f"   最多branch数: {max(branch_counts)}")
            print(f"   最少branch数: {min(branch_counts)}")
        
        # 有代码的branch数量
        try:
            branches_with_code = session.query(TraderBranch).filter(
                TraderBranch.institution_code.isnot(None)
            ).count()
            print(f"   有institution_code的branch: {branches_with_code} 个 ({branches_with_code / sql_count * 100 if sql_count > 0 else 0:.1f}%)")
        except Exception as e:
            print(f"   查询institution_code统计失败: {str(e)}")
        
        # 6. 检查唯一约束
        print(f"\n🔍 检查6: 唯一约束验证")
        try:
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
        except Exception as e:
            print(f"   ⚠️  检查唯一约束失败: {str(e)}")
        
        # 7. 检查外键完整性
        print(f"\n🔍 检查7: 外键完整性")
        try:
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
        except Exception as e:
            print(f"   ⚠️  检查外键完整性失败: {str(e)}")
        
        # 8. 显示branch数量最多的trader
        print(f"\n🔍 检查8: branch数量最多的前10个trader")
        try:
            top_traders = sorted(trader_branch_stats, key=lambda x: x[2], reverse=True)[:10]
            for trader_id, trader_name, count in top_traders:
                print(f"   {trader_name:20s}: {count:3d} 个branch")
        except Exception as e:
            print(f"   ⚠️  查询失败: {str(e)}")
        
        # 9. 总结
        print(f"\n" + "="*70)
        print("📋 检查结果总结")
        print("="*70)
        
        if sql_count > 0:
            print(f"\n✅ Supabase trader_branch表数据验证通过:")
            print(f"   - 表中有 {sql_count} 条记录")
            print(f"   - 所有 {trader_count} 个trader都有关联branch")
            print(f"   - 没有发现数据完整性问题")
        else:
            print(f"\n❌ Supabase trader_branch表中没有数据！")
            print(f"\n请运行导入脚本:")
            print(f"PYTHONPATH=. python backend/scripts/import_traders_from_file.py backend/data/traders_data.txt --force")
            print(f"\n确保 DATABASE_URL 环境变量指向 Supabase 数据库")
        
    except Exception as e:
        print(f"\n❌ 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"\n可能的原因:")
        print(f"1. DATABASE_URL 环境变量未设置或设置错误")
        print(f"2. Supabase 数据库连接失败")
        print(f"3. 网络连接问题")
        print(f"4. 数据库权限问题")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    # 显示环境变量信息（不显示敏感信息）
    print("\n📋 环境变量检查:")
    database_url = os.getenv("DATABASE_URL", "未设置")
    if database_url != "未设置":
        # 隐藏密码
        if '@' in database_url:
            parts = database_url.split('@')
            if ':' in parts[0]:
                scheme_user = parts[0].split('://')
                if len(scheme_user) > 1:
                    user_pass = scheme_user[1]
                    if ':' in user_pass:
                        user = user_pass.split(':')[0]
                        database_url_display = database_url.replace(user_pass, f"{user}:***")
                    else:
                        database_url_display = database_url
                else:
                    database_url_display = database_url
            else:
                database_url_display = database_url
        else:
            database_url_display = database_url
        print(f"   DATABASE_URL: {database_url_display[:80]}...")
    else:
        print(f"   DATABASE_URL: {database_url}")
        print(f"   ⚠️  请设置 DATABASE_URL 环境变量指向 Supabase 数据库")
    
    check_supabase_trader_branch()
