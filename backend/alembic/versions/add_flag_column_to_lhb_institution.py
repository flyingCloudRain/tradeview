"""add flag column to lhb_institution table

Revision ID: add_flag_to_lhb_institution
Revises: add_lhb_hot_institution
Create Date: 2026-01-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect


# revision identifiers, used by Alembic.
revision: str = 'add_flag_to_lhb_institution'
down_revision: Union[str, None] = 'add_lhb_hot_institution'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    检查 lhb_institution 表是否存在 flag 列，如果不存在则添加
    仅支持 PostgreSQL/Supabase 数据库
    """
    # 获取数据库连接和dialect
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    
    # 验证数据库类型
    if dialect_name != 'postgresql':
        raise ValueError(f"不支持的数据库类型: {dialect_name}。当前项目仅支持 PostgreSQL/Supabase 数据库。")
    
    # PostgreSQL: 使用 information_schema 检查列是否存在
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'lhb_institution' AND column_name = 'flag'
    """))
    column_exists = result.fetchone() is not None
    
    if not column_exists:
        # 添加 flag 列
        op.add_column('lhb_institution', sa.Column('flag', sa.String(length=10), nullable=True, comment='交易方向：买入/卖出'))
        
        # 创建索引
        try:
            op.create_index('ix_lhb_institution_flag', 'lhb_institution', ['flag'], unique=False)
        except Exception as e:
            # 如果索引已存在，忽略错误
            print(f"⚠️  索引可能已存在: {e}")
        
        # PostgreSQL 添加注释
        try:
            op.execute(text("COMMENT ON COLUMN lhb_institution.flag IS '交易方向：买入/卖出'"))
        except Exception:
            pass  # 注释可能已存在
        
        print("✅ 已添加 flag 列到 lhb_institution 表")
    else:
        print("ℹ️  lhb_institution 表已存在 flag 列，跳过")


def downgrade() -> None:
    """
    移除 flag 列（如果需要回滚）
    注意：这可能会丢失数据
    仅支持 PostgreSQL/Supabase 数据库
    """
    # 获取数据库连接和dialect
    conn = op.get_bind()
    dialect_name = conn.dialect.name
    
    # 验证数据库类型
    if dialect_name != 'postgresql':
        raise ValueError(f"不支持的数据库类型: {dialect_name}。当前项目仅支持 PostgreSQL/Supabase 数据库。")
    
    # PostgreSQL: 使用 information_schema 检查列是否存在
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'lhb_institution' AND column_name = 'flag'
    """))
    column_exists = result.fetchone() is not None
    
    if column_exists:
        # 先删除索引
        try:
            op.drop_index('ix_lhb_institution_flag', table_name='lhb_institution')
        except Exception:
            pass  # 索引可能不存在
        
        # 删除列
        op.drop_column('lhb_institution', 'flag')
        print("✅ 已移除 lhb_institution 表的 flag 列")
