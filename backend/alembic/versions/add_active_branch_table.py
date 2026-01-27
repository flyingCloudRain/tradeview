"""add_active_branch_table

Revision ID: add_active_branch
Revises: e07af5e6cdba
Create Date: 2025-01-16 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_active_branch'
down_revision = 'e07af5e6cdba'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'active_branch',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, comment='上榜日期'),
        sa.Column('institution_name', sa.String(length=200), nullable=False, comment='营业部名称'),
        sa.Column('institution_code', sa.String(length=50), nullable=True, comment='营业部代码'),
        sa.Column('buy_stock_count', sa.Integer(), nullable=True, comment='买入个股数'),
        sa.Column('sell_stock_count', sa.Integer(), nullable=True, comment='卖出个股数'),
        sa.Column('buy_amount', sa.Numeric(precision=18, scale=2), nullable=True, comment='买入总金额'),
        sa.Column('sell_amount', sa.Numeric(precision=18, scale=2), nullable=True, comment='卖出总金额'),
        sa.Column('net_amount', sa.Numeric(precision=18, scale=2), nullable=True, comment='总买卖净额'),
        sa.Column('buy_stocks', sa.Text(), nullable=True, comment='买入股票列表'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'institution_code', name='uq_active_branch'),
        comment='活跃营业部表'
    )
    op.create_index('ix_active_branch_date', 'active_branch', ['date'], unique=False)
    op.create_index('ix_active_branch_institution_name', 'active_branch', ['institution_name'], unique=False)
    op.create_index('ix_active_branch_institution_code', 'active_branch', ['institution_code'], unique=False)


def downgrade():
    op.drop_index('ix_active_branch_institution_code', table_name='active_branch')
    op.drop_index('ix_active_branch_institution_name', table_name='active_branch')
    op.drop_index('ix_active_branch_date', table_name='active_branch')
    op.drop_table('active_branch')
