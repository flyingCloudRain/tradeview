"""merge heads

Revision ID: 7494e0e4dba5
Revises: 29d3bfe76150, add_aka_column_to_trader
Create Date: 2026-01-11 14:23:37.270466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7494e0e4dba5'
down_revision: Union[str, None] = ('29d3bfe76150', 'add_aka_column_to_trader')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

