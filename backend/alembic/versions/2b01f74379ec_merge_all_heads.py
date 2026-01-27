"""merge_all_heads

Revision ID: 2b01f74379ec
Revises: add_concept_hierarchy_fields, add_flag_to_lhb_institution, add_performance_indexes, simple_add_active_branch_detail
Create Date: 2026-01-17 23:58:42.483817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b01f74379ec'
down_revision: Union[str, None] = ('add_concept_hierarchy_fields', 'add_flag_to_lhb_institution', 'add_performance_indexes', 'simple_add_active_branch_detail')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

