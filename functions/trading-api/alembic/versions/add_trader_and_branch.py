"""add trader and trader_branch tables

Revision ID: add_trader_and_branch
Revises: add_lhb_hot_institution
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_trader_and_branch'
down_revision = 'add_lhb_hot_institution'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'trader',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('aka', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_trader_name', 'trader', ['name'], unique=False)

    op.create_table(
        'trader_branch',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('trader_id', sa.Integer(), nullable=False),
        sa.Column('institution_name', sa.String(length=200), nullable=False),
        sa.Column('institution_code', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['trader_id'], ['trader.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trader_id', 'institution_name', name='uq_trader_branch_name')
    )
    op.create_index('ix_trader_branch_trader_id', 'trader_branch', ['trader_id'], unique=False)
    op.create_index('ix_trader_branch_institution_name', 'trader_branch', ['institution_name'], unique=False)
    op.create_index('ix_trader_branch_institution_code', 'trader_branch', ['institution_code'], unique=False)


def downgrade():
    op.drop_index('ix_trader_branch_institution_code', table_name='trader_branch')
    op.drop_index('ix_trader_branch_institution_name', table_name='trader_branch')
    op.drop_index('ix_trader_branch_trader_id', table_name='trader_branch')
    op.drop_table('trader_branch')
    op.drop_index('ix_trader_name', table_name='trader')
    op.drop_table('trader')

