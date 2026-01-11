"""add concept fund flow table

Revision ID: add_concept_fund_flow
Revises: add_industry_fund_flow
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_concept_fund_flow'
down_revision = 'add_industry_fund_flow'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'concept_fund_flow',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('concept', sa.String(length=200), nullable=False),
        sa.Column('index_value', sa.Numeric(12, 2), nullable=True),
        sa.Column('index_change_percent', sa.Numeric(8, 2), nullable=True),
        sa.Column('inflow', sa.Numeric(16, 2), nullable=True),
        sa.Column('outflow', sa.Numeric(16, 2), nullable=True),
        sa.Column('net_amount', sa.Numeric(16, 2), nullable=True),
        sa.Column('stock_count', sa.Numeric(10, 0), nullable=True),
        sa.Column('leader_stock', sa.String(length=100), nullable=True),
        sa.Column('leader_change_percent', sa.Numeric(8, 2), nullable=True),
        sa.Column('leader_price', sa.Numeric(12, 2), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_concept_fund_flow_date', 'concept_fund_flow', ['date'], unique=False)
    op.create_index('ix_concept_fund_flow_concept', 'concept_fund_flow', ['concept'], unique=False)


def downgrade():
    op.drop_index('ix_concept_fund_flow_concept', table_name='concept_fund_flow')
    op.drop_index('ix_concept_fund_flow_date', table_name='concept_fund_flow')
    op.drop_table('concept_fund_flow')

