#!/usr/bin/env python3
"""
简化的游资和游资机构导入脚本
可以直接执行，无需设置PYTHONPATH

使用方法:
    python3 backend/scripts/import_traders_simple.py [--force|--incremental]
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# 导入主导入函数
from scripts.import_traders_detailed import main, parse_traders_data, TRADERS_DATA


def print_usage():
    """打印使用说明"""
    print("游资和游资机构导入脚本")
    print("")
    print("使用方法:")
    print(f"  python3 {Path(__file__).name} [选项]")
    print("")
    print("选项:")
    print("  --force, -f        强制重新导入（删除并重新创建所有机构关联）")
    print("  --incremental, -i   增量导入（保留现有关联，只添加新的）")
    print("  --help, -h          显示此帮助信息")
    print("  --stats             仅显示数据统计，不执行导入")
    print("")
    print("默认: 强制重新导入模式")


def show_stats():
    """显示数据统计"""
    print("解析游资数据...")
    traders_data = parse_traders_data(TRADERS_DATA)
    
    total_branches = sum(len(trader['branches']) for trader in traders_data)
    
    print("\n" + "="*50)
    print("数据统计")
    print("="*50)
    print(f"游资主体数量: {len(traders_data)} 个")
    print(f"机构关联数量: {total_branches} 个")
    print("\n游资列表:")
    for i, trader in enumerate(traders_data, 1):
        branch_count = len(trader['branches'])
        print(f"  {i:2d}. {trader['name']:<20} ({branch_count:2d} 个机构)")
    print("="*50)


def main_cli():
    """命令行主函数"""
    # 解析命令行参数
    force_reimport = True
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['--help', '-h']:
            print_usage()
            return 0
        elif arg in ['--stats', '-s']:
            show_stats()
            return 0
        elif arg in ['--incremental', '-i']:
            force_reimport = False
            print("📝 使用增量导入模式（保留现有关联）")
        elif arg in ['--force', '-f']:
            force_reimport = True
            print("🔄 使用强制重新导入模式（删除并重新创建所有关联）")
        else:
            print(f"❌ 未知参数: {arg}")
            print_usage()
            return 1
    
    # 检查数据库连接
    print("🔍 检查数据库连接...")
    try:
        from app.database.session import engine
        with engine.connect() as conn:
            print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 错误: 无法连接到数据库: {e}")
        print("\n请检查:")
        print("  1. DATABASE_URL 环境变量是否正确设置")
        print("  2. 数据库服务是否运行")
        print("  3. 数据库表是否已创建（运行: alembic upgrade head）")
        return 1
    
    print("")
    
    # 执行导入
    try:
        main(force_reimport=force_reimport)
        return 0
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main_cli()
    sys.exit(exit_code)
