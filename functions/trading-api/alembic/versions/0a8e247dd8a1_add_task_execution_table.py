"""add_task_execution_table

Revision ID: 0a8e247dd8a1
Revises: 1068f9d65b66
Create Date: 2026-01-07 18:34:26.472391

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0a8e247dd8a1'
down_revision: Union[str, None] = '1068f9d65b66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'task_execution',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('task_name', sa.String(length=100), nullable=False, comment='任务名称'),
        sa.Column('task_type', sa.String(length=50), nullable=False, comment='任务类型'),
        sa.Column('status', sa.Enum('pending', 'running', 'success', 'failed', name='taskstatus'), nullable=False, comment='执行状态'),
        sa.Column('start_time', sa.DateTime(), nullable=False, comment='开始时间'),
        sa.Column('end_time', sa.DateTime(), nullable=True, comment='结束时间'),
        sa.Column('duration', sa.String(length=20), nullable=True, comment='执行时长（秒）'),
        sa.Column('result', sa.JSON(), nullable=True, comment='执行结果详情'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('triggered_by', sa.String(length=20), nullable=False, server_default='scheduler', comment='触发方式：scheduler/manual'),
        sa.Column('target_date', sa.String(length=20), nullable=True, comment='目标日期'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_execution_id'), 'task_execution', ['id'], unique=False)
    op.create_index('ix_task_execution_task_name', 'task_execution', ['task_name'], unique=False)
    op.create_index('ix_task_execution_task_type', 'task_execution', ['task_type'], unique=False)
    op.create_index('ix_task_execution_status', 'task_execution', ['status'], unique=False)
    op.create_table_comment('task_execution', '任务执行历史表')


def downgrade() -> None:
    op.drop_index('ix_task_execution_status', table_name='task_execution')
    op.drop_index('ix_task_execution_task_type', table_name='task_execution')
    op.drop_index('ix_task_execution_task_name', table_name='task_execution')
    op.drop_index(op.f('ix_task_execution_id'), table_name='task_execution')
    op.drop_table('task_execution')
    op.execute("DROP TYPE IF EXISTS taskstatus")

