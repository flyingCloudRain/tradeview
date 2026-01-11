"""add current_price and turnover_amount to stock_fund_flow

Revision ID: add_price_turnover_stock
Revises: add_change_pct_stock_flow
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_price_turnover_stock'
down_revision = 'add_change_pct_stock_flow'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stock_fund_flow', sa.Column('current_price', sa.Numeric(12, 2), nullable=True))
    op.add_column('stock_fund_flow', sa.Column('turnover_amount', sa.Numeric(20, 2), nullable=True))


def downgrade():
    op.drop_column('stock_fund_flow', 'turnover_amount')
    op.drop_column('stock_fund_flow', 'current_price')

