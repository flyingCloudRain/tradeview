"""add_composite_indexes_for_lhb_queries

Revision ID: 29d3bfe76150
Revises: e07af5e6cdba
Create Date: 2026-01-08 01:34:02.479280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29d3bfe76150'
down_revision: Union[str, None] = 'e07af5e6cdba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

