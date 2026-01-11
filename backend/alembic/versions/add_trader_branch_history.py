"""add trader_branch_history table

Revision ID: add_trader_branch_history
Revises: add_trader_and_branch
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_trader_branch_history'
down_revision = 'add_zt_pool_down'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'trader_branch_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('trader_branch_id', sa.Integer(), nullable=False),
        sa.Column('institution_code', sa.String(length=50), nullable=True),
        sa.Column('institution_name', sa.String(length=200), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('stock_code', sa.String(length=10), nullable=False),
        sa.Column('stock_name', sa.String(length=50), nullable=False),
        sa.Column('change_percent', sa.Numeric(8, 2), nullable=True),
        sa.Column('buy_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('sell_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('net_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('reason', sa.String(length=200), nullable=True),
        sa.Column('after_1d', sa.Numeric(8, 2), nullable=True),
        sa.Column('after_2d', sa.Numeric(8, 2), nullable=True),
        sa.Column('after_3d', sa.Numeric(8, 2), nullable=True),
        sa.Column('after_5d', sa.Numeric(8, 2), nullable=True),
        sa.Column('after_10d', sa.Numeric(8, 2), nullable=True),
        sa.Column('after_20d', sa.Numeric(8, 2), nullable=True),
        sa.Column('after_30d', sa.Numeric(8, 2), nullable=True),
        sa.ForeignKeyConstraint(['trader_branch_id'], ['trader_branch.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trader_branch_id', 'date', 'stock_code', name='uq_trader_branch_history')
    )
    op.create_index('ix_trader_branch_history_trader_branch_id', 'trader_branch_history', ['trader_branch_id'], unique=False)
    op.create_index('ix_trader_branch_history_institution_code', 'trader_branch_history', ['institution_code'], unique=False)
    op.create_index('ix_trader_branch_history_institution_name', 'trader_branch_history', ['institution_name'], unique=False)
    op.create_index('ix_trader_branch_history_date', 'trader_branch_history', ['date'], unique=False)
    op.create_index('ix_trader_branch_history_stock_code', 'trader_branch_history', ['stock_code'], unique=False)


def downgrade():
    op.drop_index('ix_trader_branch_history_stock_code', table_name='trader_branch_history')
    op.drop_index('ix_trader_branch_history_date', table_name='trader_branch_history')
    op.drop_index('ix_trader_branch_history_institution_name', table_name='trader_branch_history')
    op.drop_index('ix_trader_branch_history_institution_code', table_name='trader_branch_history')
    op.drop_index('ix_trader_branch_history_trader_branch_id', table_name='trader_branch_history')
    op.drop_table('trader_branch_history')

