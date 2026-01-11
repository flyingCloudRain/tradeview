"""add_start_time_index_to_task_execution

Revision ID: e07af5e6cdba
Revises: add_index_lhb_detail_id
Create Date: 2026-01-08 01:32:14.683817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e07af5e6cdba'
down_revision: Union[str, None] = 'add_index_lhb_detail_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 为 start_time 添加索引以优化排序查询
    op.create_index(
        'ix_task_execution_start_time',
        'task_execution',
        ['start_time'],
        unique=False
    )
    # 添加复合索引以优化 task_type + start_time 的查询
    op.create_index(
        'ix_task_execution_task_type_start_time',
        'task_execution',
        ['task_type', 'start_time'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_task_execution_task_type_start_time', table_name='task_execution')
    op.drop_index('ix_task_execution_start_time', table_name='task_execution')

