"""add stock_history table

Revision ID: add_stock_history
Revises: e07af5e6cdba
Create Date: 2026-01-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_stock_history'
down_revision: Union[str, None] = 'e07af5e6cdba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建股票历史行情表
    op.create_table(
        'stock_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, comment='日期'),
        sa.Column('stock_code', sa.String(length=20), nullable=False, comment='股票代码'),
        sa.Column('stock_name', sa.String(length=50), nullable=True, comment='股票名称'),
        sa.Column('open_price', sa.Numeric(10, 2), nullable=True, comment='开盘价'),
        sa.Column('close_price', sa.Numeric(10, 2), nullable=True, comment='收盘价'),
        sa.Column('high_price', sa.Numeric(10, 2), nullable=True, comment='最高价'),
        sa.Column('low_price', sa.Numeric(10, 2), nullable=True, comment='最低价'),
        sa.Column('volume', sa.BigInteger(), nullable=True, comment='成交量'),
        sa.Column('amount', sa.Numeric(20, 2), nullable=True, comment='成交额'),
        sa.Column('amplitude', sa.Numeric(5, 2), nullable=True, comment='振幅'),
        sa.Column('change_percent', sa.Numeric(8, 2), nullable=True, comment='涨跌幅'),
        sa.Column('change_amount', sa.Numeric(10, 2), nullable=True, comment='涨跌额'),
        sa.Column('turnover_rate', sa.Numeric(5, 2), nullable=True, comment='换手率'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_history_id'), 'stock_history', ['id'], unique=False)
    op.create_index(op.f('ix_stock_history_date'), 'stock_history', ['date'], unique=False)
    op.create_index(op.f('ix_stock_history_stock_code'), 'stock_history', ['stock_code'], unique=False)
    op.create_index('idx_stock_history_date_stock', 'stock_history', ['date', 'stock_code'], unique=False)
    op.create_index('idx_stock_history_stock_date', 'stock_history', ['stock_code', 'date'], unique=False)
    op.create_table_comment('stock_history', '股票历史行情表')


def downgrade() -> None:
    op.drop_index('idx_stock_history_stock_date', table_name='stock_history')
    op.drop_index('idx_stock_history_date_stock', table_name='stock_history')
    op.drop_index(op.f('ix_stock_history_stock_code'), table_name='stock_history')
    op.drop_index(op.f('ix_stock_history_date'), table_name='stock_history')
    op.drop_index(op.f('ix_stock_history_id'), table_name='stock_history')
    op.drop_table('stock_history')
