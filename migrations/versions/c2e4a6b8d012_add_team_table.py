"""add team table

Revision ID: c2e4a6b8d012
Revises: a1c3d5e7f901
Create Date: 2026-03-22 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c2e4a6b8d012'
down_revision = 'a1c3d5e7f901'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'teams',
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
    op.create_index('ix_teams_name', 'teams', ['name'], unique=True)


def downgrade():
    op.drop_index('ix_teams_name', table_name='teams')
    op.drop_table('teams')
