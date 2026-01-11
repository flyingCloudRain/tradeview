"""add change_percent to stock_fund_flow

Revision ID: add_change_pct_stock_flow
Revises: add_trader_branch_history
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_change_pct_stock_flow'
down_revision = 'add_trader_branch_history'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('stock_fund_flow', sa.Column('change_percent', sa.Numeric(8, 2), nullable=True))


def downgrade():
    op.drop_column('stock_fund_flow', 'change_percent')

