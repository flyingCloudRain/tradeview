"""add performance indexes

Revision ID: add_performance_indexes
Revises: dd7fc9193fd9
Create Date: 2026-01-09
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = 'dd7fc9193fd9'
branch_labels = None
depends_on = None


def upgrade():
    # 为 stock_fund_flow 表添加复合索引
    op.create_index(
        'idx_stock_fund_flow_date_stock',
        'stock_fund_flow',
        ['date', 'stock_code'],
        unique=False
    )
    op.create_index(
        'idx_stock_fund_flow_stock_date',
        'stock_fund_flow',
        ['stock_code', 'date'],
        unique=False
    )
    op.create_index(
        'idx_stock_fund_flow_date_main_net',
        'stock_fund_flow',
        ['date', 'main_net_inflow'],
        unique=False
    )
    
    # 为 zt_pool 表添加复合索引
    op.create_index(
        'idx_zt_pool_date_stock',
        'zt_pool',
        ['date', 'stock_code'],
        unique=False
    )
    op.create_index(
        'idx_zt_pool_stock_date',
        'zt_pool',
        ['stock_code', 'date'],
        unique=False
    )
    
    # 为 lhb_detail 表添加复合索引
    op.create_index(
        'idx_lhb_detail_date_stock',
        'lhb_detail',
        ['date', 'stock_code'],
        unique=False
    )
    op.create_index(
        'idx_lhb_detail_stock_date',
        'lhb_detail',
        ['stock_code', 'date'],
        unique=False
    )
    
    # 为 industry_fund_flow 表添加复合索引
    op.create_index(
        'idx_industry_fund_flow_date_industry',
        'industry_fund_flow',
        ['date', 'industry'],
        unique=False
    )
    op.create_index(
        'idx_industry_fund_flow_date_net',
        'industry_fund_flow',
        ['date', 'net_amount'],
        unique=False
    )
    
    # 为 concept_fund_flow 表添加复合索引
    op.create_index(
        'idx_concept_fund_flow_date_concept',
        'concept_fund_flow',
        ['date', 'concept'],
        unique=False
    )
    op.create_index(
        'idx_concept_fund_flow_date_net',
        'concept_fund_flow',
        ['date', 'net_amount'],
        unique=False
    )


def downgrade():
    # 删除所有添加的索引
    op.drop_index('idx_concept_fund_flow_date_net', table_name='concept_fund_flow')
    op.drop_index('idx_concept_fund_flow_date_concept', table_name='concept_fund_flow')
    op.drop_index('idx_industry_fund_flow_date_net', table_name='industry_fund_flow')
    op.drop_index('idx_industry_fund_flow_date_industry', table_name='industry_fund_flow')
    op.drop_index('idx_lhb_detail_stock_date', table_name='lhb_detail')
    op.drop_index('idx_lhb_detail_date_stock', table_name='lhb_detail')
    op.drop_index('idx_zt_pool_stock_date', table_name='zt_pool')
    op.drop_index('idx_zt_pool_date_stock', table_name='zt_pool')
    op.drop_index('idx_stock_fund_flow_date_main_net', table_name='stock_fund_flow')
    op.drop_index('idx_stock_fund_flow_stock_date', table_name='stock_fund_flow')
    op.drop_index('idx_stock_fund_flow_date_stock', table_name='stock_fund_flow')
