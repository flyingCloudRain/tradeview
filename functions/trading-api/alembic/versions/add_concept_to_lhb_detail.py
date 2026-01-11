"""add concept to lhb_detail

Revision ID: add_concept_to_lhb_detail
Revises: 
Create Date: 2025-01-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_concept_to_lhb_detail'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加 concept 字段到 lhb_detail 表，若已存在则跳过
    op.execute("ALTER TABLE lhb_detail ADD COLUMN IF NOT EXISTS concept VARCHAR(200)")


def downgrade():
    # 删除 concept 字段
    op.drop_column('lhb_detail', 'concept')

