"""add_new_fields_to_limit_up_board

Revision ID: 4257c18c1e14
Revises: add_stock_history
Create Date: 2026-01-14 01:12:23.473502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4257c18c1e14'
down_revision: Union[str, None] = 'add_stock_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加涨跌幅字段（单位：%）
    op.add_column('limit_up_board', sa.Column('price_change_pct', sa.Numeric(precision=10, scale=2), nullable=True, comment='涨跌幅（%）'))
    
    # 添加最新价字段
    op.add_column('limit_up_board', sa.Column('latest_price', sa.Numeric(precision=10, scale=2), nullable=True, comment='最新价'))
    
    # 添加成交额字段
    op.add_column('limit_up_board', sa.Column('turnover', sa.Numeric(precision=20, scale=0), nullable=True, comment='成交额'))
    
    # 添加总市值字段（亿元）
    op.add_column('limit_up_board', sa.Column('total_market_value', sa.Numeric(precision=15, scale=2), nullable=True, comment='总市值（亿元）'))
    
    # 添加换手率字段（单位：%）
    op.add_column('limit_up_board', sa.Column('turnover_rate', sa.Numeric(precision=10, scale=2), nullable=True, comment='换手率（%）'))
    
    # 添加封板资金字段
    op.add_column('limit_up_board', sa.Column('sealing_capital', sa.Numeric(precision=20, scale=0), nullable=True, comment='封板资金'))
    
    # 添加首次封板时间字段（格式：09:25:00）
    op.add_column('limit_up_board', sa.Column('first_sealing_time', sa.Time(), nullable=True, comment='首次封板时间（格式：09:25:00）'))
    
    # 添加最后封板时间字段（格式：09:25:00）
    op.add_column('limit_up_board', sa.Column('last_sealing_time', sa.Time(), nullable=True, comment='最后封板时间（格式：09:25:00）'))
    
    # 添加炸板次数字段
    op.add_column('limit_up_board', sa.Column('board_breaking_count', sa.Integer(), nullable=True, comment='炸板次数'))
    
    # 添加涨停统计字段
    op.add_column('limit_up_board', sa.Column('limit_up_statistics', sa.String(length=100), nullable=True, comment='涨停统计'))
    
    # 添加连板数字段（1为首板）
    op.add_column('limit_up_board', sa.Column('consecutive_board_count', sa.Integer(), nullable=True, comment='连板数（1为首板）'))
    
    # 添加所属行业字段
    op.add_column('limit_up_board', sa.Column('industry', sa.String(length=100), nullable=True, comment='所属行业'))
    
    # 为行业字段创建索引
    op.create_index(op.f('ix_limit_up_board_industry'), 'limit_up_board', ['industry'], unique=False)


def downgrade() -> None:
    # 删除行业字段索引
    op.drop_index(op.f('ix_limit_up_board_industry'), table_name='limit_up_board')
    
    # 删除所有新增字段
    op.drop_column('limit_up_board', 'industry')
    op.drop_column('limit_up_board', 'consecutive_board_count')
    op.drop_column('limit_up_board', 'limit_up_statistics')
    op.drop_column('limit_up_board', 'board_breaking_count')
    op.drop_column('limit_up_board', 'last_sealing_time')
    op.drop_column('limit_up_board', 'first_sealing_time')
    op.drop_column('limit_up_board', 'sealing_capital')
    op.drop_column('limit_up_board', 'turnover_rate')
    op.drop_column('limit_up_board', 'total_market_value')
    op.drop_column('limit_up_board', 'turnover')
    op.drop_column('limit_up_board', 'latest_price')
    op.drop_column('limit_up_board', 'price_change_pct')

