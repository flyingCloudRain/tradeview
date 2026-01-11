"""add index on lhb_institution.lhb_detail_id

Revision ID: add_index_lhb_detail_id
Revises: b8b3389db151
Create Date: 2026-01-08
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_index_lhb_detail_id'
down_revision = 'b8b3389db151'
branch_labels = None
depends_on = None


def upgrade():
    # 添加索引以提高查询性能
    # 如果索引已存在，SQLite会忽略，PostgreSQL会报错但可以手动处理
    try:
        op.create_index(
            'ix_lhb_institution_lhb_detail_id',
            'lhb_institution',
            ['lhb_detail_id'],
            unique=False
        )
    except Exception as e:
        # 如果索引已存在，记录警告但继续
        print(f"Warning: Index might already exist: {e}")


def downgrade():
    op.drop_index('ix_lhb_institution_lhb_detail_id', table_name='lhb_institution')

