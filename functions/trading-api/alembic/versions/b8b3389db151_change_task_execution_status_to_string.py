"""change_task_execution_status_to_string

Revision ID: b8b3389db151
Revises: 0a8e247dd8a1
Create Date: 2026-01-07 18:45:11.878173

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8b3389db151'
down_revision: Union[str, None] = '0a8e247dd8a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 将status列从enum类型改为varchar类型
    # PostgreSQL需要先转换为text，再转换为varchar
    op.execute("""
        ALTER TABLE task_execution 
        ALTER COLUMN status TYPE VARCHAR(20) 
        USING status::text
    """)


def downgrade() -> None:
    # 恢复为enum类型
    op.execute("""
        ALTER TABLE task_execution 
        ALTER COLUMN status TYPE taskstatus 
        USING status::taskstatus
    """)

