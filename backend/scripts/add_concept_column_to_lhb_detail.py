#!/usr/bin/env python3
"""
添加 concept 列到 lhb_detail 表
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
from sqlalchemy import create_engine, text
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


def add_concept_column():
    """添加 concept 列到 lhb_detail 表"""
    try:
        # PostgreSQL/Supabase: 使用 IF NOT EXISTS
        logger.info("检测到 PostgreSQL/Supabase 数据库")
        with engine.begin() as conn:
            alter_sql = "ALTER TABLE lhb_detail ADD COLUMN IF NOT EXISTS concept VARCHAR(200)"
            logger.info("正在添加 concept 列...")
            conn.execute(text(alter_sql))
            logger.info("成功添加 concept 列到 lhb_detail 表")
        
        return True
            
    except Exception as e:
        logger.error(f"添加列失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("开始添加 concept 列到 lhb_detail 表...")
    success = add_concept_column()
    if success:
        logger.info("操作完成")
        sys.exit(0)
    else:
        logger.error("操作失败")
        sys.exit(1)
