"""merge limit_up_board and stock_concept heads

Revision ID: 4d13f3ece43f
Revises: add_limit_up_board, add_stock_concept_tables
Create Date: 2026-01-11 20:51:28.983795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d13f3ece43f'
down_revision: Union[str, None] = ('add_limit_up_board', 'add_stock_concept_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

