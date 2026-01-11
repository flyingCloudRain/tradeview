"""change trader aka comment from 别名 to 描述

Revision ID: change_trader_aka_comment
Revises: add_price_and_is_executed
Create Date: 2026-01-10 00:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'change_trader_aka_comment'
down_revision: Union[str, None] = 'add_price_and_is_executed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 注释在模型定义中已更新
    # 此迁移文件仅用于记录模型变更历史
    # 实际注释更改在 app/models/lhb.py 中的 Trader 模型中
    pass


def downgrade() -> None:
    # 恢复操作：注释已在模型定义中处理
    pass
