#!/usr/bin/env python3
"""
添加 flag 列到 lhb_institution 表
用于修复数据库结构问题
仅支持 PostgreSQL/Supabase 数据库
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

# 必须设置 DATABASE_URL 环境变量（Supabase PostgreSQL）
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ 错误: DATABASE_URL 环境变量未设置")
    print("请设置 DATABASE_URL 环境变量指向 Supabase 数据库:")
    print('  export DATABASE_URL="postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"')
    sys.exit(1)

# 验证数据库URL是否为PostgreSQL
if not database_url.lower().startswith('postgresql://'):
    print(f"❌ 错误: 不支持的数据库类型。当前项目仅支持 PostgreSQL/Supabase 数据库。")
    print(f"当前 DATABASE_URL: {database_url[:50]}...")
    sys.exit(1)

# 创建 PostgreSQL/Supabase 引擎
from sqlalchemy import create_engine, text, inspect
import logging

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=10,
    echo=False,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_flag_column():
    """添加 flag 列到 lhb_institution 表"""
    print("=" * 70)
    print("添加 flag 列到 lhb_institution 表")
    print("=" * 70)
    print(f"数据库: {database_url}")
    print()
    
    with engine.connect() as conn:
        # 检查表是否存在
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'lhb_institution' not in tables:
            print("❌ 错误: lhb_institution 表不存在")
            return False
        
        # 检查列是否存在
        columns = [col['name'] for col in inspector.get_columns('lhb_institution')]
        print(f"📋 lhb_institution 表现有列: {', '.join(columns)}")
        
        if 'flag' in columns:
            print("\n✅ flag 列已存在，无需添加")
            return True
        
        # 添加列
        print("\n添加 flag 列...")
        try:
            # 使用 begin() 来管理事务（自动提交或回滚）
            with engine.begin() as conn:
                # PostgreSQL/Supabase: 使用 IF NOT EXISTS
                conn.execute(text("ALTER TABLE lhb_institution ADD COLUMN IF NOT EXISTS flag VARCHAR(10)"))
                conn.execute(text("COMMENT ON COLUMN lhb_institution.flag IS '交易方向：买入/卖出'"))
            
            # 创建索引
            try:
                with engine.begin() as conn:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lhb_institution_flag ON lhb_institution(flag)"))
            except Exception as e:
                print(f"⚠️  创建索引时出现警告（可能已存在）: {e}")
            
            print("✅ 已成功添加 flag 列")
            
            # 验证
            columns_after = [col['name'] for col in inspector.get_columns('lhb_institution')]
            if 'flag' in columns_after:
                print(f"\n✅ 验证成功: flag 列已添加到 lhb_institution 表")
                print(f"📋 更新后的列: {', '.join(columns_after)}")
                return True
            else:
                print("\n❌ 验证失败: flag 列未成功添加")
                return False
                
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = add_flag_column()
    sys.exit(0 if success else 1)
