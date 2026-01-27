"""merge_active_branch_and_other_heads

Revision ID: 82aa768422cc
Revises: 4257c18c1e14, add_active_branch, inst_trading_stats
Create Date: 2026-01-17 15:14:34.476845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82aa768422cc'
down_revision: Union[str, None] = ('4257c18c1e14', 'add_active_branch', 'inst_trading_stats')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

