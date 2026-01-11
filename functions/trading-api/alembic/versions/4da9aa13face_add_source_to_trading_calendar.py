"""add_source_to_trading_calendar

Revision ID: 4da9aa13face
Revises: merge_trading_calendar_flags
Create Date: 2026-01-07 15:37:11.528020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4da9aa13face'
down_revision: Union[str, None] = 'merge_trading_calendar_flags'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('trading_calendar', sa.Column('source', sa.String(length=100), nullable=True, comment='来源'))


def downgrade() -> None:
    op.drop_column('trading_calendar', 'source')

