"""
详细检查游资机构branch数据问题
执行：PYTHONPATH=. python backend/scripts/check_traders_branch_data.py
"""
import sys
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.models.lhb import Trader, TraderBranch
from sqlalchemy import func, and_, or_


def check_traders_branch_data():
    """详细检查游资机构branch数据"""
    print("="*70)
    print("🔍 游资机构Branch数据详细检查")
    print("="*70)
    
    session = SessionLocal()
    try:
        # 1. 基本统计
        trader_count = session.query(Trader).count()
        branch_count = session.query(TraderBranch).count()
        
        print(f"\n📊 基本统计:")
        print(f"   游资主体总数: {trader_count} 个")
        print(f"   机构关联总数: {branch_count} 个")
        
        # 2. 检查没有机构的游资
        traders_without_branches = session.query(Trader).filter(
            ~Trader.branches.any()
        ).all()
        
        if traders_without_branches:
            print(f"\n❌ 问题1: 没有关联机构的游资 ({len(traders_without_branches)} 个):")
            for trader in traders_without_branches:
                print(f"   - {trader.name}")
        else:
            print(f"\n✅ 检查1: 所有游资都有关联机构")
        
        # 3. 检查重复的机构名称（同一游资内）
        print(f"\n🔍 检查2: 同一游资内的重复机构名称")
        duplicate_in_trader = []
        traders = session.query(Trader).all()
        for trader in traders:
            branches = session.query(TraderBranch).filter(
                TraderBranch.trader_id == trader.id
            ).all()
            branch_names = [b.institution_name for b in branches]
            seen = set()
            duplicates = []
            for name in branch_names:
                if name in seen:
                    duplicates.append(name)
                seen.add(name)
            if duplicates:
                duplicate_in_trader.append((trader.name, duplicates))
        
        if duplicate_in_trader:
            print(f"   ❌ 发现 {len(duplicate_in_trader)} 个游资存在重复机构:")
            for trader_name, dup_names in duplicate_in_trader:
                print(f"   - {trader_name}: {', '.join(set(dup_names))}")
        else:
            print(f"   ✅ 没有发现同一游资内的重复机构")
        
        # 4. 检查机构代码
        branches_with_code = session.query(TraderBranch).filter(
            TraderBranch.institution_code.isnot(None)
        ).count()
        branches_without_code = branch_count - branches_with_code
        
        print(f"\n🔍 检查3: 机构代码完整性")
        print(f"   有代码: {branches_with_code} 个 ({branches_with_code / branch_count * 100 if branch_count > 0 else 0:.1f}%)")
        print(f"   无代码: {branches_without_code} 个 ({branches_without_code / branch_count * 100 if branch_count > 0 else 0:.1f}%)")
        
        if branches_without_code == branch_count:
            print(f"   ⚠️  警告: 所有机构关联都没有代码")
        
        # 5. 检查空值或空白字符串
        print(f"\n🔍 检查4: 空值或空白字符串")
        empty_name_branches = session.query(TraderBranch).filter(
            or_(
                TraderBranch.institution_name.is_(None),
                TraderBranch.institution_name == '',
                TraderBranch.institution_name.like(' %')
            )
        ).all()
        
        if empty_name_branches:
            print(f"   ❌ 发现 {len(empty_name_branches)} 个机构名称为空或空白:")
            for branch in empty_name_branches[:10]:
                trader = session.query(Trader).filter(Trader.id == branch.trader_id).first()
                print(f"   - 游资: {trader.name if trader else 'Unknown'}, 机构名称: '{branch.institution_name}'")
        else:
            print(f"   ✅ 没有发现空值或空白字符串")
        
        # 6. 检查机构名称格式（前后空格）
        print(f"\n🔍 检查5: 机构名称格式问题（前后空格）")
        branches_with_spaces = session.query(TraderBranch).filter(
            or_(
                TraderBranch.institution_name.like(' %'),
                TraderBranch.institution_name.like('% ')
            )
        ).all()
        
        if branches_with_spaces:
            print(f"   ⚠️  发现 {len(branches_with_spaces)} 个机构名称有前后空格:")
            for branch in branches_with_spaces[:10]:
                trader = session.query(Trader).filter(Trader.id == branch.trader_id).first()
                print(f"   - 游资: {trader.name if trader else 'Unknown'}, 机构: '{branch.institution_name}'")
        else:
            print(f"   ✅ 没有发现前后空格问题")
        
        # 7. 检查同一机构关联到多个游资的情况（这是正常的，但需要统计）
        print(f"\n🔍 检查6: 机构关联到多个游资的情况（正常情况）")
        duplicate_branches = session.query(
            TraderBranch.institution_name,
            func.count(TraderBranch.id).label('count')
        ).group_by(TraderBranch.institution_name).having(
            func.count(TraderBranch.id) > 1
        ).order_by(func.count(TraderBranch.id).desc()).all()
        
        if duplicate_branches:
            print(f"   📋 发现 {len(duplicate_branches)} 个机构关联到多个游资（这是正常的）:")
            print(f"   前10个最常见的机构:")
            for inst_name, count in duplicate_branches[:10]:
                # 查找关联的游资
                traders = session.query(Trader.name).join(
                    TraderBranch, Trader.id == TraderBranch.trader_id
                ).filter(
                    TraderBranch.institution_name == inst_name
                ).all()
                trader_names = ", ".join([t[0] for t in traders])
                print(f"   - {inst_name}: 关联到 {count} 个游资")
                print(f"     游资: {trader_names}")
        else:
            print(f"   ✅ 没有机构关联到多个游资")
        
        # 8. 检查数据完整性：对比文件数据和数据库数据
        print(f"\n🔍 检查7: 对比文件数据和数据库数据")
        mismatched = []
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
            
            print(f"   文件中的游资数量: {len(file_traders)} 个")
            
            # 对比数据库数据
            db_traders = {}
            for trader in session.query(Trader).all():
                branches = session.query(TraderBranch).filter(
                    TraderBranch.trader_id == trader.id
                ).all()
                db_traders[trader.name] = [b.institution_name for b in branches]
            
            print(f"   数据库中的游资数量: {len(db_traders)} 个")
            
            # 检查文件中有但数据库中没有的游资
            file_only = set(file_traders.keys()) - set(db_traders.keys())
            if file_only:
                print(f"   ⚠️  文件中有但数据库中没有的游资 ({len(file_only)} 个):")
                for name in file_only:
                    print(f"   - {name}")
            else:
                print(f"   ✅ 文件中的所有游资都在数据库中")
            
            # 检查数据库中有但文件中没有的游资
            db_only = set(db_traders.keys()) - set(file_traders.keys())
            if db_only:
                print(f"   ⚠️  数据库中有但文件中没有的游资 ({len(db_only)} 个):")
                for name in db_only:
                    print(f"   - {name}")
            else:
                print(f"   ✅ 数据库中的所有游资都在文件中")
            
            # 检查机构数量不一致的游资
            common_traders = set(file_traders.keys()) & set(db_traders.keys())
            print(f"   共同游资数量: {len(common_traders)} 个")
            
            for name in common_traders:
                file_count = len(file_traders[name])
                db_count = len(db_traders[name])
                if file_count != db_count:
                    mismatched.append((name, file_count, db_count))
            
            if mismatched:
                print(f"   ⚠️  机构数量不一致的游资 ({len(mismatched)} 个):")
                for name, file_count, db_count in mismatched[:10]:
                    print(f"   - {name}: 文件 {file_count} 个, 数据库 {db_count} 个")
                    # 显示差异
                    file_insts = set(file_traders[name])
                    db_insts = set(db_traders[name])
                    missing_in_db = file_insts - db_insts
                    extra_in_db = db_insts - file_insts
                    if missing_in_db:
                        print(f"     数据库缺少: {', '.join(list(missing_in_db)[:3])}")
                    if extra_in_db:
                        print(f"     数据库多余: {', '.join(list(extra_in_db)[:3])}")
            else:
                print(f"   ✅ 所有游资的机构数量都一致")
        else:
            print(f"   ⚠️  数据文件不存在: {data_file}")
        
        # 9. 检查外键完整性
        print(f"\n🔍 检查8: 外键完整性")
        orphan_branches = session.query(TraderBranch).filter(
            ~TraderBranch.trader_id.in_(
                session.query(Trader.id)
            )
        ).all()
        
        if orphan_branches:
            print(f"   ❌ 发现 {len(orphan_branches)} 个孤立机构关联（trader_id不存在）:")
            for branch in orphan_branches[:10]:
                print(f"   - 机构: {branch.institution_name}, trader_id: {branch.trader_id}")
        else:
            print(f"   ✅ 没有发现孤立机构关联")
        
        # 10. 统计信息汇总
        print(f"\n" + "="*70)
        print("📋 检查结果汇总")
        print("="*70)
        
        issues = []
        if traders_without_branches:
            issues.append(f"❌ {len(traders_without_branches)} 个游资没有关联机构")
        if duplicate_in_trader:
            issues.append(f"❌ {len(duplicate_in_trader)} 个游资存在重复机构")
        if empty_name_branches:
            issues.append(f"❌ {len(empty_name_branches)} 个机构名称为空")
        if branches_with_spaces:
            issues.append(f"⚠️  {len(branches_with_spaces)} 个机构名称有前后空格")
        if mismatched:
            issues.append(f"⚠️  {len(mismatched)} 个游资的机构数量与文件不一致")
        if orphan_branches:
            issues.append(f"❌ {len(orphan_branches)} 个孤立机构关联")
        
        if issues:
            print("\n发现的问题:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✅ 没有发现数据问题！")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    check_traders_branch_data()
