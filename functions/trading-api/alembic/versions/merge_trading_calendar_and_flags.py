"""merge trading_calendar and flags branches

Revision ID: merge_trading_calendar_flags
Revises: add_flags_stock_flow, add_trading_calendar
Create Date: 2025-01-15
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_trading_calendar_flags'
down_revision = ('add_flags_stock_flow', 'add_trading_calendar')
branch_labels = None
depends_on = None


def upgrade():
    # 这是一个合并迁移，两个分支都已经应用了各自的更改
    # 这里不需要做任何操作，只是合并分支
    pass


def downgrade():
    # 合并迁移的降级也不需要操作
    pass

