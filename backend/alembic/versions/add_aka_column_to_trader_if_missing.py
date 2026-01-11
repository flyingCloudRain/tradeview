"""add aka column to trader table if missing

Revision ID: add_aka_column_to_trader
Revises: change_trader_aka_comment
Create Date: 2026-01-10 02:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'add_aka_column_to_trader'
down_revision: Union[str, None] = 'change_trader_aka_comment'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    检查 trader 表是否存在 aka 列，如果不存在则添加
    适用于 PostgreSQL 数据库
    """
    # 获取数据库连接
    conn = op.get_bind()
    
    # 检查列是否存在（PostgreSQL）
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'trader' AND column_name = 'aka'
    """))
    
    column_exists = result.fetchone() is not None
    
    if not column_exists:
        # 添加 aka 列
        op.add_column('trader', sa.Column('aka', sa.Text(), nullable=True))
        # PostgreSQL 添加注释
        op.execute(text("COMMENT ON COLUMN trader.aka IS '描述'"))
        print("✅ 已添加 aka 列到 trader 表")
    else:
        print("ℹ️  trader 表已存在 aka 列，跳过")


def downgrade() -> None:
    """
    移除 aka 列（如果需要回滚）
    注意：这可能会丢失数据
    """
    # 获取数据库连接
    conn = op.get_bind()
    
    # 检查列是否存在
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'trader' AND column_name = 'aka'
    """))
    
    column_exists = result.fetchone() is not None
    
    if column_exists:
        op.drop_column('trader', 'aka')
        print("✅ 已移除 trader 表的 aka 列")
