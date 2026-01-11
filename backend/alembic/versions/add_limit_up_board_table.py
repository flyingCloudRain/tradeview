"""add limit_up_board table

Revision ID: add_limit_up_board
Revises: e07af5e6cdba
Create Date: 2025-01-20
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_limit_up_board'
down_revision = 'e07af5e6cdba'
branch_labels = None
depends_on = None


def upgrade():
    # 创建涨停板分析表
    op.create_table(
        'limit_up_board',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False, comment='日期'),
        sa.Column('board_name', sa.String(length=100), nullable=False, comment='板块名称'),
        sa.Column('board_stock_count', sa.Integer(), nullable=True, comment='板块股票数量'),
        sa.Column('stock_code', sa.String(length=20), nullable=False, comment='股票代码'),
        sa.Column('stock_name', sa.String(length=50), nullable=False, comment='股票名称'),
        sa.Column('limit_up_days', sa.String(length=20), nullable=True, comment='涨停天数（如：11 天 9 板）'),
        sa.Column('limit_up_time', sa.Time(), nullable=True, comment='涨停时间'),
        sa.Column('circulation_market_value', sa.Numeric(15, 2), nullable=True, comment='流通市值（亿元）'),
        sa.Column('turnover_amount', sa.Numeric(15, 2), nullable=True, comment='成交额（亿元）'),
        sa.Column('keywords', sa.Text(), nullable=True, comment='涨停关键词（原始文本）'),
        sa.Column('limit_up_reason', sa.Text(), nullable=True, comment='涨停原因（解析后的主要原因）'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='涨停标签列表（从关键字解析）'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_limit_up_board_id'), 'limit_up_board', ['id'], unique=False)
    op.create_index(op.f('ix_limit_up_board_date'), 'limit_up_board', ['date'], unique=False)
    op.create_index(op.f('ix_limit_up_board_board_name'), 'limit_up_board', ['board_name'], unique=False)
    op.create_index(op.f('ix_limit_up_board_stock_code'), 'limit_up_board', ['stock_code'], unique=False)
    op.create_index(op.f('ix_limit_up_board_stock_name'), 'limit_up_board', ['stock_name'], unique=False)
    op.create_index('idx_date_board', 'limit_up_board', ['date', 'board_name'], unique=False)
    op.create_index('idx_date_stock', 'limit_up_board', ['date', 'stock_code'], unique=False)
    op.create_table_comment('limit_up_board', '涨停板分析表')
    
    # 创建涨停板分析概念板块关联表
    op.create_table(
        'limit_up_board_concept',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('limit_up_board_id', sa.Integer(), nullable=False),
        sa.Column('concept_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['concept_id'], ['stock_concept.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['limit_up_board_id'], ['limit_up_board.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_limit_up_board_concept_id'), 'limit_up_board_concept', ['id'], unique=False)
    op.create_index(op.f('ix_limit_up_board_concept_limit_up_board_id'), 'limit_up_board_concept', ['limit_up_board_id'], unique=False)
    op.create_index(op.f('ix_limit_up_board_concept_concept_id'), 'limit_up_board_concept', ['concept_id'], unique=False)
    op.create_index('idx_limit_up_board_concept', 'limit_up_board_concept', ['limit_up_board_id', 'concept_id'], unique=True)
    op.create_table_comment('limit_up_board_concept', '涨停板分析概念板块关联表')


def downgrade():
    op.drop_table('limit_up_board_concept')
    op.drop_index('idx_date_stock', table_name='limit_up_board')
    op.drop_index('idx_date_board', table_name='limit_up_board')
    op.drop_index(op.f('ix_limit_up_board_stock_name'), table_name='limit_up_board')
    op.drop_index(op.f('ix_limit_up_board_stock_code'), table_name='limit_up_board')
    op.drop_index(op.f('ix_limit_up_board_board_name'), table_name='limit_up_board')
    op.drop_index(op.f('ix_limit_up_board_date'), table_name='limit_up_board')
    op.drop_index(op.f('ix_limit_up_board_id'), table_name='limit_up_board')
    op.drop_table('limit_up_board')
