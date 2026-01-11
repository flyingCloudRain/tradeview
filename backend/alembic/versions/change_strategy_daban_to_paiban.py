"""change strategy from 打板 to 排板

Revision ID: change_strategy_daban_to_paiban
Revises: 1068f9d65b66
Create Date: 2026-01-09 15:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'change_strategy_daban_to_paiban'
down_revision: Union[str, None] = '1068f9d65b66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 更新现有数据：将"打板"改为"排板"
    op.execute("""
        UPDATE trading_calendar 
        SET strategy = '排板' 
        WHERE strategy = '打板'
    """)
    
    # 更新列注释
    # SQLite不支持直接修改列注释，但可以通过重建表来实现
    # 这里我们只更新数据，注释会在模型定义中更新


def downgrade():
    # 恢复数据：将"排板"改回"打板"
    op.execute("""
        UPDATE trading_calendar 
        SET strategy = '打板' 
        WHERE strategy = '排板'
    """)

