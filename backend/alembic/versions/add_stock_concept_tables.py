"""add stock concept tables

Revision ID: add_stock_concept_tables
Revises: 7494e0e4dba5
Create Date: 2026-01-11 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_stock_concept_tables'
down_revision: Union[str, None] = '7494e0e4dba5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建概念板块表
    op.create_table(
        'stock_concept',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='概念板块名称'),
        sa.Column('code', sa.String(length=20), nullable=True, comment='概念板块代码'),
        sa.Column('description', sa.Text(), nullable=True, comment='概念板块描述'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_stock_concept_id'), 'stock_concept', ['id'], unique=False)
    op.create_index('idx_concept_name', 'stock_concept', ['name'], unique=False)
    op.create_index('idx_concept_code', 'stock_concept', ['code'], unique=False)
    op.create_table_comment('stock_concept', '股票概念板块表')
    
    # 创建股票概念关联表（核心表）
    op.create_table(
        'stock_concept_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('stock_name', sa.String(length=50), nullable=False, comment='股票名称'),
        sa.Column('concept_id', sa.Integer(), nullable=False, comment='概念板块ID'),
        sa.ForeignKeyConstraint(['concept_id'], ['stock_concept.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stock_name', 'concept_id', name='uq_stock_concept_mapping')
    )
    op.create_index(op.f('ix_stock_concept_mapping_id'), 'stock_concept_mapping', ['id'], unique=False)
    op.create_index('idx_scm_stock', 'stock_concept_mapping', ['stock_name'], unique=False)
    op.create_index('idx_scm_concept', 'stock_concept_mapping', ['concept_id'], unique=False)
    op.create_table_comment('stock_concept_mapping', '股票概念板块通用关联表（核心表，供所有模块使用）')
    
    # 可选：创建交易日历概念板块关联表（用于覆盖或补充）
    op.create_table(
        'trading_calendar_concept',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('trading_calendar_id', sa.Integer(), nullable=False, comment='交易日历ID'),
        sa.Column('concept_id', sa.Integer(), nullable=False, comment='概念板块ID'),
        sa.ForeignKeyConstraint(['concept_id'], ['stock_concept.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trading_calendar_id'], ['trading_calendar.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trading_calendar_id', 'concept_id', name='uq_trading_calendar_concept')
    )
    op.create_index(op.f('ix_trading_calendar_concept_id'), 'trading_calendar_concept', ['id'], unique=False)
    op.create_index('idx_tcc_calendar', 'trading_calendar_concept', ['trading_calendar_id'], unique=False)
    op.create_index('idx_tcc_concept', 'trading_calendar_concept', ['concept_id'], unique=False)
    op.create_table_comment('trading_calendar_concept', '交易日历概念板块关联表（可选，用于覆盖或补充）')


def downgrade() -> None:
    op.drop_table('trading_calendar_concept')
    op.drop_table('stock_concept_mapping')
    op.drop_table('stock_concept')
