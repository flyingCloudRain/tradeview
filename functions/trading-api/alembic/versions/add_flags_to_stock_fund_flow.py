"""add is_limit_up and is_lhb flags to stock_fund_flow

Revision ID: add_flags_stock_flow
Revises: add_price_turnover_stock
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_flags_stock_flow'
down_revision = 'add_price_turnover_stock'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stock_fund_flow', sa.Column('is_limit_up', sa.Boolean(), nullable=True, default=False))
    op.add_column('stock_fund_flow', sa.Column('is_lhb', sa.Boolean(), nullable=True, default=False))


def downgrade():
    op.drop_column('stock_fund_flow', 'is_lhb')
    op.drop_column('stock_fund_flow', 'is_limit_up')

