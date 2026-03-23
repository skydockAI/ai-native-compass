"""add template tables

Revision ID: d3f5a7b9c012
Revises: c2e4a6b8d012
Create Date: 2026-03-22 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd3f5a7b9c012'
down_revision = 'c2e4a6b8d012'
branch_labels = None
depends_on = None


def upgrade():
    # repo_templates
    op.create_table(
        'repo_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_repo_templates_name', 'repo_templates', ['name'], unique=True)

    # template_artifacts
    op.create_table(
        'template_artifacts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column(
            'type',
            sa.Enum('document', 'skill', 'agent', 'other', name='artifacttype'),
            nullable=False,
        ),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'value_type',
            sa.Enum('text', 'number', 'boolean', 'list', name='artifactvaluetype'),
            nullable=True,
        ),
        sa.Column('is_required', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['repo_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_template_artifacts_template_id', 'template_artifacts', ['template_id'])

    # artifact_list_options
    op.create_table(
        'artifact_list_options',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('artifact_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['artifact_id'], ['template_artifacts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_artifact_list_options_artifact_id', 'artifact_list_options', ['artifact_id']
    )


def downgrade():
    op.drop_index('ix_artifact_list_options_artifact_id', table_name='artifact_list_options')
    op.drop_table('artifact_list_options')
    op.drop_index('ix_template_artifacts_template_id', table_name='template_artifacts')
    op.drop_table('template_artifacts')
    op.drop_enum = getattr(op, 'drop_type', None)
    op.execute('DROP TYPE IF EXISTS artifactvaluetype')
    op.execute('DROP TYPE IF EXISTS artifacttype')
    op.drop_index('ix_repo_templates_name', table_name='repo_templates')
    op.drop_table('repo_templates')
