"""
验证游资机构信息导入结果
执行：PYTHONPATH=. python backend/scripts/verify_traders_import.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.models.lhb import Trader, TraderBranch
from sqlalchemy import func


def verify_traders_import():
    """验证游资机构信息导入结果"""
    print("="*70)
    print("📊 游资机构信息验证报告")
    print("="*70)
    
    session = SessionLocal()
    try:
        # 基本统计
        trader_count = session.query(Trader).count()
        branch_count = session.query(TraderBranch).count()
        
        print(f"\n✅ 基本统计:")
        print(f"   游资主体总数: {trader_count} 个")
        print(f"   机构关联总数: {branch_count} 个")
        print(f"   平均每个游资关联机构数: {branch_count / trader_count if trader_count > 0 else 0:.2f} 个")
        
        # 机构数量分布
        trader_branch_stats = session.query(
            Trader.name,
            Trader.aka,
            func.count(TraderBranch.id).label('branch_count')
        ).join(
            TraderBranch, Trader.id == TraderBranch.trader_id, isouter=True
        ).group_by(Trader.id, Trader.name, Trader.aka).order_by(
            func.count(TraderBranch.id).desc()
        ).all()
        
        print(f"\n📈 机构数量分布（前15名）:")
        for i, (name, aka, count) in enumerate(trader_branch_stats[:15], 1):
            aka_preview = (aka[:30] + "...") if aka and len(aka) > 30 else (aka or "")
            print(f"  {i:2d}. {name:20s} - {count:3d} 个机构 | {aka_preview}")
        
        # 检查没有机构的游资
        traders_without_branches = session.query(Trader).filter(
            ~Trader.branches.any()
        ).all()
        
        if traders_without_branches:
            print(f"\n⚠️  没有关联机构的游资 ({len(traders_without_branches)} 个):")
            for trader in traders_without_branches:
                print(f"  - {trader.name}")
        else:
            print(f"\n✅ 所有游资都有关联机构")
        
        # 检查有机构代码的关联
        branches_with_code = session.query(TraderBranch).filter(
            TraderBranch.institution_code.isnot(None)
        ).count()
        
        branches_without_code = branch_count - branches_with_code
        
        print(f"\n📋 机构代码统计:")
        print(f"   有代码的机构关联: {branches_with_code} 个 ({branches_with_code / branch_count * 100 if branch_count > 0 else 0:.1f}%)")
        print(f"   无代码的机构关联: {branches_without_code} 个 ({branches_without_code / branch_count * 100 if branch_count > 0 else 0:.1f}%)")
        
        # 检查重复的机构名称（同一机构关联到多个游资）
        duplicate_branches = session.query(
            TraderBranch.institution_name,
            func.count(TraderBranch.id).label('count')
        ).group_by(TraderBranch.institution_name).having(
            func.count(TraderBranch.id) > 1
        ).order_by(func.count(TraderBranch.id).desc()).all()
        
        if duplicate_branches:
            print(f"\n📋 重复关联的机构名称（前10个）:")
            for inst_name, count in duplicate_branches[:10]:
                # 查找关联的游资
                traders = session.query(Trader.name).join(
                    TraderBranch, Trader.id == TraderBranch.trader_id
                ).filter(
                    TraderBranch.institution_name == inst_name
                ).all()
                trader_names = ", ".join([t[0] for t in traders])
                print(f"  - {inst_name}: 关联到 {count} 个游资")
                print(f"    游资: {trader_names}")
        
        # 显示一些示例数据
        print(f"\n📝 示例数据（前3个游资的详细信息）:")
        sample_traders = session.query(Trader).limit(3).all()
        for trader in sample_traders:
            print(f"\n  【{trader.name}】")
            if trader.aka:
                print(f"    说明: {trader.aka[:100]}{'...' if trader.aka and len(trader.aka) > 100 else ''}")
            branches = session.query(TraderBranch).filter(
                TraderBranch.trader_id == trader.id
            ).limit(5).all()
            if branches:
                print(f"    关联机构（前5个）:")
                for branch in branches:
                    code_info = f" [{branch.institution_code}]" if branch.institution_code else ""
                    print(f"      - {branch.institution_name}{code_info}")
                total_branches = session.query(TraderBranch).filter(
                    TraderBranch.trader_id == trader.id
                ).count()
                if total_branches > 5:
                    print(f"      ... 还有 {total_branches - 5} 个机构")
            else:
                print(f"    关联机构: 无")
        
        print("\n" + "="*70)
        print("✅ 验证完成")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    verify_traders_import()
