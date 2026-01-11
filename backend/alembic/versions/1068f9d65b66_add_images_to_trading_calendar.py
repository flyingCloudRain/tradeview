"""add_images_to_trading_calendar

Revision ID: 1068f9d65b66
Revises: 4da9aa13face
Create Date: 2026-01-07 18:33:20.160112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1068f9d65b66'
down_revision: Union[str, None] = '4da9aa13face'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('trading_calendar', sa.Column('images', sa.JSON(), nullable=True, comment='图片URL列表'))


def downgrade() -> None:
    op.drop_column('trading_calendar', 'images')

