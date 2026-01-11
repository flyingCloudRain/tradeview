"""add lhb hot institution table

Revision ID: add_lhb_hot_institution
Revises: add_concept_to_lhb_detail
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'add_lhb_hot_institution'
down_revision = 'add_concept_to_lhb_detail'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'lhb_hot_institution',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('institution_name', sa.String(length=200), nullable=False),
        sa.Column('institution_code', sa.String(length=50), nullable=True),
        sa.Column('buy_stock_count', sa.Integer(), nullable=True),
        sa.Column('sell_stock_count', sa.Integer(), nullable=True),
        sa.Column('buy_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('sell_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('net_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('buy_stocks', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lhb_hot_institution_date', 'lhb_hot_institution', ['date'], unique=False)
    op.create_index('ix_lhb_hot_institution_institution_name', 'lhb_hot_institution', ['institution_name'], unique=False)
    op.create_index('ix_lhb_hot_institution_institution_code', 'lhb_hot_institution', ['institution_code'], unique=False)


def downgrade():
    op.drop_index('ix_lhb_hot_institution_institution_code', table_name='lhb_hot_institution')
    op.drop_index('ix_lhb_hot_institution_institution_name', table_name='lhb_hot_institution')
    op.drop_index('ix_lhb_hot_institution_date', table_name='lhb_hot_institution')
    op.drop_table('lhb_hot_institution')

