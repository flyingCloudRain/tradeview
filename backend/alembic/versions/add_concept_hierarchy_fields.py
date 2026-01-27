"""add concept hierarchy fields

Revision ID: add_concept_hierarchy_fields
Revises: add_stock_concept_tables
Create Date: 2026-01-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_concept_hierarchy_fields'
down_revision: Union[str, None] = '4d13f3ece43f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加层级相关字段
    op.add_column('stock_concept', sa.Column('parent_id', sa.Integer(), nullable=True, comment='父概念ID，NULL表示一级概念'))
    op.add_column('stock_concept', sa.Column('level', sa.Integer(), nullable=False, server_default='1', comment='层级：1=一级，2=二级，3=三级'))
    op.add_column('stock_concept', sa.Column('path', sa.String(length=500), nullable=True, comment='层级路径，如：1/5/12'))
    op.add_column('stock_concept', sa.Column('sort_order', sa.Integer(), server_default='0', comment='同级排序顺序'))
    op.add_column('stock_concept', sa.Column('stock_count', sa.Integer(), server_default='0', comment='关联的个股数量（冗余字段）'))
    
    # 添加外键约束
    op.create_foreign_key(
        'fk_concept_parent',
        'stock_concept', 'stock_concept',
        ['parent_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # 添加检查约束
    op.create_check_constraint(
        'check_level_range',
        'stock_concept',
        'level IN (1, 2, 3)'
    )
    
    op.create_check_constraint(
        'check_level_parent',
        'stock_concept',
        '(parent_id IS NULL AND level = 1) OR (parent_id IS NOT NULL AND level > 1)'
    )
    
    # 初始化现有数据：将所有现有概念设置为一级，path 设置为 id
    op.execute("""
        UPDATE stock_concept 
        SET level = 1, path = id::text 
        WHERE path IS NULL;
    """)
    
    # 创建索引
    op.create_index('idx_concept_parent', 'stock_concept', ['parent_id'], unique=False)
    op.create_index('idx_concept_level', 'stock_concept', ['level'], unique=False)
    op.create_index('idx_concept_path', 'stock_concept', ['path'], unique=False)
    
    # 创建唯一索引（同一父概念下名称唯一）
    op.create_index('idx_concept_name_level_parent', 'stock_concept', ['name', 'level', 'parent_id'], unique=True)


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_concept_name_level_parent', table_name='stock_concept')
    op.drop_index('idx_concept_path', table_name='stock_concept')
    op.drop_index('idx_concept_level', table_name='stock_concept')
    op.drop_index('idx_concept_parent', table_name='stock_concept')
    
    # 删除约束
    op.drop_constraint('check_level_parent', 'stock_concept', type_='check')
    op.drop_constraint('check_level_range', 'stock_concept', type_='check')
    
    # 删除外键
    op.drop_constraint('fk_concept_parent', 'stock_concept', type_='foreignkey')
    
    # 删除字段
    op.drop_column('stock_concept', 'stock_count')
    op.drop_column('stock_concept', 'sort_order')
    op.drop_column('stock_concept', 'path')
    op.drop_column('stock_concept', 'level')
    op.drop_column('stock_concept', 'parent_id')
