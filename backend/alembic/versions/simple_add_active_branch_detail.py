"""simple_add_active_branch_detail

Revision ID: simple_add_active_branch_detail
Revises: 82aa768422cc
Create Date: 2026-01-17 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'simple_add_active_branch_detail'
down_revision: Union[str, None] = '82aa768422cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 只创建 active_branch_detail 表
    op.create_table('active_branch_detail',
    sa.Column('institution_code', sa.String(length=50), nullable=False, comment='营业部代码'),
    sa.Column('institution_name', sa.String(length=200), nullable=True, comment='营业部名称'),
    sa.Column('date', sa.Date(), nullable=False, comment='交易日期'),
    sa.Column('stock_code', sa.String(length=10), nullable=False, comment='股票代码'),
    sa.Column('stock_name', sa.String(length=50), nullable=False, comment='股票名称'),
    sa.Column('change_percent', sa.Numeric(precision=8, scale=2), nullable=True, comment='涨跌幅'),
    sa.Column('buy_amount', sa.Numeric(precision=18, scale=2), nullable=True, comment='买入金额'),
    sa.Column('sell_amount', sa.Numeric(precision=18, scale=2), nullable=True, comment='卖出金额'),
    sa.Column('net_amount', sa.Numeric(precision=18, scale=2), nullable=True, comment='净额'),
    sa.Column('reason', sa.String(length=200), nullable=True, comment='上榜原因'),
    sa.Column('after_1d', sa.Numeric(precision=8, scale=2), nullable=True, comment='1日后涨跌幅'),
    sa.Column('after_2d', sa.Numeric(precision=8, scale=2), nullable=True, comment='2日后涨跌幅'),
    sa.Column('after_3d', sa.Numeric(precision=8, scale=2), nullable=True, comment='3日后涨跌幅'),
    sa.Column('after_5d', sa.Numeric(precision=8, scale=2), nullable=True, comment='5日后涨跌幅'),
    sa.Column('after_10d', sa.Numeric(precision=8, scale=2), nullable=True, comment='10日后涨跌幅'),
    sa.Column('after_20d', sa.Numeric(precision=8, scale=2), nullable=True, comment='20日后涨跌幅'),
    sa.Column('after_30d', sa.Numeric(precision=8, scale=2), nullable=True, comment='30日后涨跌幅'),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('institution_code', 'date', 'stock_code', name='uq_active_branch_detail'),
    comment='活跃营业部交易详情表'
    )
    op.create_index(op.f('ix_active_branch_detail_date'), 'active_branch_detail', ['date'], unique=False)
    op.create_index(op.f('ix_active_branch_detail_id'), 'active_branch_detail', ['id'], unique=False)
    op.create_index(op.f('ix_active_branch_detail_institution_code'), 'active_branch_detail', ['institution_code'], unique=False)
    op.create_index(op.f('ix_active_branch_detail_institution_name'), 'active_branch_detail', ['institution_name'], unique=False)
    op.create_index(op.f('ix_active_branch_detail_stock_code'), 'active_branch_detail', ['stock_code'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_active_branch_detail_stock_code'), table_name='active_branch_detail')
    op.drop_index(op.f('ix_active_branch_detail_institution_name'), table_name='active_branch_detail')
    op.drop_index(op.f('ix_active_branch_detail_institution_code'), table_name='active_branch_detail')
    op.drop_index(op.f('ix_active_branch_detail_id'), table_name='active_branch_detail')
    op.drop_index(op.f('ix_active_branch_detail_date'), table_name='active_branch_detail')
    op.drop_table('active_branch_detail')
