"""add_institution_trading_statistics_table

Revision ID: add_institution_trading_statistics
Revises: e07af5e6cdba
Create Date: 2025-01-16 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'inst_trading_stats'
down_revision = 'e07af5e6cdba'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'institution_trading_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, comment='上榜日期'),
        sa.Column('stock_code', sa.String(length=10), nullable=False, comment='股票代码'),
        sa.Column('stock_name', sa.String(length=50), nullable=False, comment='股票名称'),
        sa.Column('close_price', sa.Numeric(precision=10, scale=2), nullable=True, comment='收盘价'),
        sa.Column('change_percent', sa.Numeric(precision=5, scale=2), nullable=True, comment='涨跌幅'),
        sa.Column('buyer_institution_count', sa.Integer(), nullable=True, comment='买方机构数'),
        sa.Column('seller_institution_count', sa.Integer(), nullable=True, comment='卖方机构数'),
        sa.Column('institution_buy_amount', sa.Numeric(precision=18, scale=2), nullable=True, comment='机构买入总额'),
        sa.Column('institution_sell_amount', sa.Numeric(precision=18, scale=2), nullable=True, comment='机构卖出总额'),
        sa.Column('institution_net_buy_amount', sa.Numeric(precision=18, scale=2), nullable=True, comment='机构买入净额'),
        sa.Column('market_total_amount', sa.Numeric(precision=18, scale=2), nullable=True, comment='市场总成交额'),
        sa.Column('net_buy_ratio', sa.Numeric(precision=8, scale=4), nullable=True, comment='机构净买额占总成交额比'),
        sa.Column('turnover_rate', sa.Numeric(precision=8, scale=4), nullable=True, comment='换手率'),
        sa.Column('circulation_market_value', sa.Numeric(precision=18, scale=2), nullable=True, comment='流通市值'),
        sa.Column('reason', sa.String(length=200), nullable=True, comment='上榜原因'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'stock_code', name='uq_institution_trading_statistics'),
        comment='机构交易统计表'
    )
    op.create_index('ix_institution_trading_statistics_date', 'institution_trading_statistics', ['date'], unique=False)
    op.create_index('ix_institution_trading_statistics_stock_code', 'institution_trading_statistics', ['stock_code'], unique=False)


def downgrade():
    op.drop_index('ix_institution_trading_statistics_stock_code', table_name='institution_trading_statistics')
    op.drop_index('ix_institution_trading_statistics_date', table_name='institution_trading_statistics')
    op.drop_table('institution_trading_statistics')
