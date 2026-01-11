"""add trading_calendar table

Revision ID: add_trading_calendar
Revises: add_change_pct_stock_flow
Create Date: 2025-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = 'add_trading_calendar'
down_revision = 'add_change_pct_stock_flow'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'trading_calendar',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('stock_name', sa.String(length=50), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False, comment='操作方向：买入/卖出'),
        sa.Column('strategy', sa.String(length=20), nullable=False, comment='策略：低吸/打板'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trading_calendar_id'), 'trading_calendar', ['id'], unique=False)
    op.create_index(op.f('ix_trading_calendar_date'), 'trading_calendar', ['date'], unique=False)
    op.create_table_comment('trading_calendar', '交易日历表')


def downgrade():
    op.drop_index(op.f('ix_trading_calendar_date'), table_name='trading_calendar')
    op.drop_index(op.f('ix_trading_calendar_id'), table_name='trading_calendar')
    op.drop_table('trading_calendar')

