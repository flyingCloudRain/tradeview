"""add price and is_executed to trading_calendar

Revision ID: add_price_and_is_executed
Revises: change_strategy_daban_to_paiban
Create Date: 2026-01-09 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_price_and_is_executed'
down_revision: Union[str, None] = 'change_strategy_daban_to_paiban'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加价格字段
    op.add_column('trading_calendar', sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True, comment='价格'))
    
    # 添加是否执行策略字段
    op.add_column('trading_calendar', sa.Column('is_executed', sa.Boolean(), nullable=True, server_default='0', comment='是否执行策略'))


def downgrade() -> None:
    op.drop_column('trading_calendar', 'is_executed')
    op.drop_column('trading_calendar', 'price')
