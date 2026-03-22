"""add user table

Revision ID: a1c3d5e7f901
Revises: b5d83f12f16e
Create Date: 2026-03-22 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a1c3d5e7f901'
down_revision = 'b5d83f12f16e'
branch_labels = None
depends_on = None


def upgrade():
    # role is stored as VARCHAR (native_enum=False) — no PostgreSQL ENUM type needed.
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column(
            'role',
            sa.Enum('ADMIN', 'EDITOR', 'VIEWER', name='userrole', native_enum=False),
            nullable=False,
        ),
        sa.Column('is_seeded', sa.Boolean(), server_default='false', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)


def downgrade():
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
