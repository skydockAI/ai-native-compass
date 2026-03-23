"""add shared attribute tables

Revision ID: e4f6a8c0d123
Revises: d3f5a7b9c012
Create Date: 2026-03-23 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e4f6a8c0d123'
down_revision = 'd3f5a7b9c012'
branch_labels = None
depends_on = None


def upgrade():
    # shared_attribute_definitions
    op.create_table(
        'shared_attribute_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_shared_attribute_definitions_name', 'shared_attribute_definitions', ['name'], unique=True)

    # repository_shared_attribute_values
    op.create_table(
        'repository_shared_attribute_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['attribute_id'], ['shared_attribute_definitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id', 'attribute_id', name='uq_repo_shared_attr'),
    )
    op.create_index(
        'ix_repository_shared_attribute_values_repository_id',
        'repository_shared_attribute_values',
        ['repository_id'],
    )
    op.create_index(
        'ix_repository_shared_attribute_values_attribute_id',
        'repository_shared_attribute_values',
        ['attribute_id'],
    )


def downgrade():
    op.drop_index(
        'ix_repository_shared_attribute_values_attribute_id',
        table_name='repository_shared_attribute_values',
    )
    op.drop_index(
        'ix_repository_shared_attribute_values_repository_id',
        table_name='repository_shared_attribute_values',
    )
    op.drop_table('repository_shared_attribute_values')
    op.drop_index('ix_shared_attribute_definitions_name', table_name='shared_attribute_definitions')
    op.drop_table('shared_attribute_definitions')
