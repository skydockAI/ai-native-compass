"""add repository tables

Revision ID: f5a7b9c1d234
Revises: e4f6a8c0d123
Create Date: 2026-03-23 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f5a7b9c1d234'
down_revision = 'e4f6a8c0d123'
branch_labels = None
depends_on = None


def upgrade():
    # repositories
    op.create_table(
        'repositories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['template_id'], ['repo_templates.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url', name='uq_repositories_url'),
    )
    op.create_index('ix_repositories_team_id', 'repositories', ['team_id'])
    op.create_index('ix_repositories_template_id', 'repositories', ['template_id'])
    op.create_index('ix_repositories_is_archived', 'repositories', ['is_archived'])

    # repository_artifact_values
    op.create_table(
        'repository_artifact_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('template_artifact_id', sa.Integer(), nullable=False),
        sa.Column('value_text', sa.Text(), nullable=True),
        sa.Column('value_number', sa.Numeric(18, 6), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_list_option_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_artifact_id'], ['template_artifacts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['value_list_option_id'], ['artifact_list_options.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id', 'template_artifact_id', name='uq_repo_artifact_value'),
    )
    op.create_index('ix_repository_artifact_values_repository_id', 'repository_artifact_values', ['repository_id'])
    op.create_index('ix_repository_artifact_values_template_artifact_id', 'repository_artifact_values', ['template_artifact_id'])
    op.create_index('ix_repository_artifact_values_value_list_option_id', 'repository_artifact_values', ['value_list_option_id'])

    # product_repository (M:N association table — linking UI in DI-009)
    # product_id has no FK to products.id here; products table is created in DI-009.
    # The FK will be added in DI-009's migration (same pattern as DI-006/DI-007 for
    # repository_shared_attribute_values.repository_id).
    op.create_table(
        'product_repository',
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('product_id', 'repository_id', name='uq_product_repository'),
    )
    op.create_index('ix_product_repository_product_id', 'product_repository', ['product_id'])
    op.create_index('ix_product_repository_repository_id', 'product_repository', ['repository_id'])

    # Add FK on repository_shared_attribute_values.repository_id → repositories.id
    # (column existed since DI-006 but FK was deferred until the repositories table existed)
    op.create_foreign_key(
        'fk_repo_shared_attr_values_repository_id',
        'repository_shared_attribute_values',
        'repositories',
        ['repository_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade():
    op.drop_constraint(
        'fk_repo_shared_attr_values_repository_id',
        'repository_shared_attribute_values',
        type_='foreignkey',
    )

    op.drop_index('ix_product_repository_repository_id', table_name='product_repository')
    op.drop_index('ix_product_repository_product_id', table_name='product_repository')
    op.drop_table('product_repository')

    op.drop_index('ix_repository_artifact_values_value_list_option_id', table_name='repository_artifact_values')
    op.drop_index('ix_repository_artifact_values_template_artifact_id', table_name='repository_artifact_values')
    op.drop_index('ix_repository_artifact_values_repository_id', table_name='repository_artifact_values')
    op.drop_table('repository_artifact_values')

    op.drop_index('ix_repositories_is_archived', table_name='repositories')
    op.drop_index('ix_repositories_template_id', table_name='repositories')
    op.drop_index('ix_repositories_team_id', table_name='repositories')
    op.drop_table('repositories')
