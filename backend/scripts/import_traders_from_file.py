"""
从文件导入游资机构信息
执行：PYTHONPATH=. python backend/scripts/import_traders_from_file.py [文件路径]
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal, engine
from app.models.lhb import Trader, TraderBranch
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


def parse_traders_data(data_text: str) -> list:
    """解析游资数据文本"""
    traders = []
    lines = data_text.strip().split('\n')
    
    # 跳过表头行
    header_patterns = ["游资信息解析存储数据库名称", "名称", "说明", "关联机构"]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 跳过表头行
        if any(pattern in line for pattern in header_patterns) and len(line.split('\t')) <= 3:
            # 检查是否是纯表头行（不包含实际数据）
            if line in ["游资信息解析存储数据库名称\t说明\t关联机构", "名称\t说明\t关联机构"] or (line.startswith("名称") and "说明" in line and "关联机构" in line):
                continue
        
        # 使用制表符分割：名称、说明、机构列表
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        
        name = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else ""
        institutions_str = parts[2].strip() if len(parts) > 2 else ""
        
        # 清理描述中的换行符
        description = description.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ').strip()
        
        # 解析机构列表（支持顿号、逗号分隔）
        institutions = []
        if institutions_str:
            # 先按顿号分割
            for inst in institutions_str.split('、'):
                # 再按逗号分割
                for inst2 in inst.split(','):
                    inst_name = inst2.strip()
                    if inst_name:
                        institutions.append({"name": inst_name, "code": None})
        
        traders.append({
            "name": name,
            "description": description,
            "branches": institutions
        })
    
    return traders


def find_institution_code(db, institution_name: str) -> str | None:
    """从现有数据中查找机构代码"""
    from app.models.lhb import TraderBranch
    
    # 精确匹配
    branch = db.query(TraderBranch).filter(
        TraderBranch.institution_name == institution_name
    ).first()
    
    if branch and branch.institution_code:
        return branch.institution_code
    
    # 模糊匹配（包含关系）
    branch = db.query(TraderBranch).filter(
        TraderBranch.institution_name.like(f"%{institution_name}%")
    ).first()
    
    if branch and branch.institution_code:
        return branch.institution_code
    
    return None


def upsert_trader(session, name: str, description: str, branches: list, force_reimport: bool = False):
    """更新或插入游资数据
    
    Args:
        session: 数据库会话
        name: 游资名称
        description: 游资说明
        branches: 营业部列表
        force_reimport: 是否强制重新导入（删除旧关联后重新创建）
    """
    # 先刷新会话，确保看到最新的数据库状态
    session.expire_all()
    
    trader = session.query(Trader).filter(Trader.name == name).first()
    
    if not trader:
        # 创建新游资
        trader = Trader(name=name, aka=description)
        session.add(trader)
        session.flush()
        print(f"✅ 创建游资: {name}")
    else:
        # 更新说明
        trader.aka = description
        print(f"🔄 更新游资: {name}")
        
        # 如果强制重新导入，删除所有旧的营业部关联
        if force_reimport:
            deleted_count = session.query(TraderBranch).filter(
                TraderBranch.trader_id == trader.id
            ).delete(synchronize_session=False)
            if deleted_count > 0:
                print(f"  🗑️  删除 {deleted_count} 个旧机构关联")
            session.flush()
    
    added_count = 0
    skipped_count = 0
    seen_names = set()  # 用于去重
    
    for inst in branches:
        inst_name = (inst.get("name") or "").strip()
        inst_code = inst.get("code")
        
        if not inst_name:
            continue
        
        # 去重：跳过已处理的机构名称
        if inst_name in seen_names:
            skipped_count += 1
            continue
        
        seen_names.add(inst_name)
        
        # 如果代码为空，尝试从现有数据中查找
        if not inst_code:
            inst_code = find_institution_code(session, inst_name)
        
        # 如果强制重新导入，直接创建新关联
        if force_reimport:
            branch = TraderBranch(
                trader_id=trader.id,
                institution_name=inst_name,
                institution_code=inst_code,
            )
            session.add(branch)
            added_count += 1
        else:
            # 检查是否已存在
            existing = session.query(TraderBranch).filter(
                TraderBranch.trader_id == trader.id,
                TraderBranch.institution_name == inst_name
            ).first()
            
            if existing:
                # 更新代码（如果之前没有）
                if not existing.institution_code and inst_code:
                    existing.institution_code = inst_code
                    print(f"  🔄 更新机构代码: {inst_name} -> {inst_code}")
                skipped_count += 1
            else:
                # 创建新关联
                branch = TraderBranch(
                    trader_id=trader.id,
                    institution_name=inst_name,
                    institution_code=inst_code,
                )
                session.add(branch)
                added_count += 1
    
    session.flush()
    if force_reimport:
        print(f"  📊 {name}: 重新导入 {added_count} 个机构")
    else:
        print(f"  📊 {name}: 新增 {added_count} 个机构，跳过 {skipped_count} 个")
    
    return added_count, skipped_count


def verify_import(session):
    """验证导入结果"""
    print("\n" + "="*60)
    print("📊 导入结果验证")
    print("="*60)
    
    trader_count = session.query(Trader).count()
    branch_count = session.query(TraderBranch).count()
    
    print(f"\n✅ 游资主体总数: {trader_count} 个")
    print(f"✅ 机构关联总数: {branch_count} 个")
    
    # 统计每个游资的机构数量
    from sqlalchemy import func
    trader_branch_stats = session.query(
        Trader.name,
        func.count(TraderBranch.id).label('branch_count')
    ).join(
        TraderBranch, Trader.id == TraderBranch.trader_id, isouter=True
    ).group_by(Trader.id, Trader.name).order_by(
        func.count(TraderBranch.id).desc()
    ).all()
    
    print(f"\n📈 机构数量分布（前10名）:")
    for i, (name, count) in enumerate(trader_branch_stats[:10], 1):
        print(f"  {i:2d}. {name}: {count} 个机构")
    
    # 检查没有机构的游资
    traders_without_branches = session.query(Trader).filter(
        ~Trader.branches.any()
    ).all()
    
    if traders_without_branches:
        print(f"\n⚠️  没有关联机构的游资 ({len(traders_without_branches)} 个):")
        for trader in traders_without_branches[:10]:
            print(f"  - {trader.name}")
        if len(traders_without_branches) > 10:
            print(f"  ... 还有 {len(traders_without_branches) - 10} 个")
    
    # 检查重复的机构名称
    from sqlalchemy import func
    duplicate_branches = session.query(
        TraderBranch.institution_name,
        func.count(TraderBranch.id).label('count')
    ).group_by(TraderBranch.institution_name).having(
        func.count(TraderBranch.id) > 1
    ).all()
    
    if duplicate_branches:
        print(f"\n📋 重复关联的机构名称 ({len(duplicate_branches)} 个):")
        for inst_name, count in duplicate_branches[:10]:
            print(f"  - {inst_name}: 关联到 {count} 个游资")
        if len(duplicate_branches) > 10:
            print(f"  ... 还有 {len(duplicate_branches) - 10} 个")
    
    print("\n" + "="*60)


def main(file_path: str, force_reimport: bool = False):
    """主函数
    
    Args:
        file_path: 数据文件路径
        force_reimport: 是否强制重新导入所有机构关联（默认False）
    """
    # 读取文件
    data_file = Path(file_path)
    if not data_file.exists():
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📂 读取文件: {file_path}")
    with open(data_file, 'r', encoding='utf-8') as f:
        data_text = f.read()
    
    print("开始解析游资数据...")
    traders_data = parse_traders_data(data_text)
    print(f"解析完成，共 {len(traders_data)} 个游资")
    
    if force_reimport:
        print("⚠️  强制重新导入模式：将删除并重新创建所有机构关联\n")
    else:
        print("📝 增量导入模式：只添加新的数据，不删除现有数据\n")
    
    session = SessionLocal()
    try:
        # 先检查数据库当前状态
        check_engine = create_engine(str(engine.url), pool_pre_ping=True)
        CheckSessionLocal = sessionmaker(autoflush=False, bind=check_engine)
        check_db = CheckSessionLocal()
        try:
            actual_trader_count = check_db.query(Trader).count()
            actual_branch_count = check_db.query(TraderBranch).count()
            print(f"📊 数据库当前状态:")
            print(f"   游资主体: {actual_trader_count} 个")
            print(f"   机构关联: {actual_branch_count} 个\n")
        finally:
            check_db.close()
            check_engine.dispose()
        
        total_added = 0
        total_skipped = 0
        
        for i, trader_data in enumerate(traders_data, 1):
            print(f"[{i}/{len(traders_data)}] 处理: {trader_data['name']}")
            try:
                added, skipped = upsert_trader(
                    session,
                    name=trader_data['name'],
                    description=trader_data['description'],
                    branches=trader_data['branches'],
                    force_reimport=force_reimport
                )
                total_added += added
                total_skipped += skipped
            except Exception as e:
                print(f"  ❌ 处理 {trader_data['name']} 时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                session.rollback()
                raise
        
        # 提交事务
        print(f"\n🔄 准备提交事务...")
        try:
            session.flush()
            session.commit()
            print(f"✅ 事务已提交")
        except Exception as e:
            print(f"❌ 提交失败: {str(e)}")
            import traceback
            traceback.print_exc()
            session.rollback()
            raise
        
        # 验证导入结果
        verify_import(session)
        
        print(f"\n✅ 导入完成!")
        print(f"   游资主体: {len(traders_data)} 个")
        if force_reimport:
            print(f"   重新导入机构关联: {total_added} 个")
        else:
            print(f"   新增机构关联: {total_added} 个")
            print(f"   跳过机构关联: {total_skipped} 个")
    except Exception as e:
        print(f"\n❌ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        if session:
            session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='从文件导入游资机构信息')
    parser.add_argument('file_path', nargs='?', 
                       default='backend/data/traders_data.txt',
                       help='数据文件路径（默认: backend/data/traders_data.txt）')
    parser.add_argument('--force', action='store_true',
                       help='强制重新导入（删除旧关联后重新创建）')
    
    args = parser.parse_args()
    
    main(args.file_path, force_reimport=args.force)
