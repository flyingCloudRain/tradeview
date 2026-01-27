"""add_task_execution_performance_indexes

Revision ID: 70379e507ece
Revises: 2b01f74379ec
Create Date: 2026-01-23 19:33:53.486283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70379e507ece'
down_revision: Union[str, None] = '2b01f74379ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 status + start_time 复合索引，优化按状态查询最新记录的性能
    # 用于 get_task_status_summary 中查询成功执行记录
    op.create_index(
        'ix_task_execution_status_start_time',
        'task_execution',
        ['status', 'start_time'],
        unique=False
    )
    
    # 添加 task_type + status + start_time 复合索引，优化按任务类型和状态查询的性能
    # 用于 get_task_executions 中按任务类型和状态过滤查询
    op.create_index(
        'ix_task_execution_task_type_status_start_time',
        'task_execution',
        ['task_type', 'status', 'start_time'],
        unique=False
    )
    
    # 添加 task_name + start_time 复合索引，优化按任务名称查询的性能
    # 用于 get_task_executions 中按任务名称过滤查询
    op.create_index(
        'ix_task_execution_task_name_start_time',
        'task_execution',
        ['task_name', 'start_time'],
        unique=False
    )


def downgrade() -> None:
    # 删除添加的索引
    op.drop_index('ix_task_execution_task_name_start_time', table_name='task_execution')
    op.drop_index('ix_task_execution_task_type_status_start_time', table_name='task_execution')
    op.drop_index('ix_task_execution_status_start_time', table_name='task_execution')

