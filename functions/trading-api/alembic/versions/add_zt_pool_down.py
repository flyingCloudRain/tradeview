"""add zt_pool_down table

Revision ID: add_zt_pool_down
Revises: add_concept_fund_flow
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_zt_pool_down'
down_revision = 'add_concept_fund_flow'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'zt_pool_down',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('stock_code', sa.String(length=10), nullable=False),
        sa.Column('stock_name', sa.String(length=50), nullable=False),
        sa.Column('change_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('latest_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('turnover_amount', sa.BigInteger(), nullable=True),
        sa.Column('circulation_market_value', sa.Numeric(15, 2), nullable=True),
        sa.Column('total_market_value', sa.Numeric(15, 2), nullable=True),
        sa.Column('turnover_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('limit_up_capital', sa.BigInteger(), nullable=True),
        sa.Column('first_limit_time', sa.Time(), nullable=True),
        sa.Column('last_limit_time', sa.Time(), nullable=True),
        sa.Column('explosion_count', sa.Integer(), nullable=True),
        sa.Column('limit_up_statistics', sa.Text(), nullable=True),
        sa.Column('consecutive_limit_count', sa.Integer(), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('concept', sa.Text(), nullable=True),
        sa.Column('limit_up_reason', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_zt_pool_down_date', 'zt_pool_down', ['date'], unique=False)
    op.create_index('ix_zt_pool_down_stock_code', 'zt_pool_down', ['stock_code'], unique=False)
    op.create_index('ix_zt_pool_down_industry', 'zt_pool_down', ['industry'], unique=False)


def downgrade():
    op.drop_index('ix_zt_pool_down_industry', table_name='zt_pool_down')
    op.drop_index('ix_zt_pool_down_stock_code', table_name='zt_pool_down')
    op.drop_index('ix_zt_pool_down_date', table_name='zt_pool_down')
    op.drop_table('zt_pool_down')

