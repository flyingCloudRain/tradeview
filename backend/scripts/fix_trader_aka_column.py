"""
修复 trader 表缺少 aka 列的问题
执行：PYTHONPATH=. python backend/scripts/fix_trader_aka_column.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from app.database.session import SessionLocal, engine


def fix_trader_aka_column():
    """检查并添加 trader 表的 aka 列（如果不存在）"""
    db = SessionLocal()
    try:
        print("=" * 50)
        print("修复 trader 表 aka 列")
        print("=" * 50)
        
        # 检查表是否存在
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'trader' not in tables:
            print("❌ 错误: trader 表不存在")
            return False
        
        # 检查列是否存在
        columns = [col['name'] for col in inspector.get_columns('trader')]
        print(f"\n📋 trader 表现有列: {', '.join(columns)}")
        
        if 'aka' in columns:
            print("\n✅ aka 列已存在，无需修复")
            return True
        
        # 获取数据库类型
        db_url = str(engine.url)
        is_postgresql = 'postgresql' in db_url or 'postgres' in db_url
        is_sqlite = 'sqlite' in db_url
        
        print(f"\n🔧 数据库类型: {'PostgreSQL' if is_postgresql else 'SQLite' if is_sqlite else 'Unknown'}")
        
        # 添加列
        if is_postgresql:
            print("\n添加 aka 列（PostgreSQL）...")
            db.execute(text("ALTER TABLE trader ADD COLUMN IF NOT EXISTS aka TEXT"))
            db.execute(text("COMMENT ON COLUMN trader.aka IS '描述'"))
        elif is_sqlite:
            print("\n添加 aka 列（SQLite）...")
            # SQLite 不支持 IF NOT EXISTS，需要先检查
            db.execute(text("ALTER TABLE trader ADD COLUMN aka TEXT"))
        else:
            print("\n⚠️  未知数据库类型，尝试通用 SQL...")
            db.execute(text("ALTER TABLE trader ADD COLUMN aka TEXT"))
        
        db.commit()
        print("✅ 已成功添加 aka 列")
        
        # 验证
        columns_after = [col['name'] for col in inspector.get_columns('trader')]
        if 'aka' in columns_after:
            print(f"\n✅ 验证成功: aka 列已添加到 trader 表")
            print(f"📋 更新后的列: {', '.join(columns_after)}")
            return True
        else:
            print("\n❌ 验证失败: aka 列未成功添加")
            return False
            
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = fix_trader_aka_column()
    sys.exit(0 if success else 1)
