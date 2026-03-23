"""add product table

Revision ID: g6b8c0d2e345
Revises: f5a7b9c1d234
Create Date: 2026-03-23 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'g6b8c0d2e345'
down_revision = 'f5a7b9c1d234'
branch_labels = None
depends_on = None


def upgrade():
    # products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_products_name'),
    )
    op.create_index('ix_products_is_archived', 'products', ['is_archived'])

    # Add FK constraint product_id → products.id on product_repository
    # (column existed since DI-007 but FK was deferred until the products table existed)
    op.create_foreign_key(
        'fk_product_repository_product_id',
        'product_repository',
        'products',
        ['product_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade():
    op.drop_constraint(
        'fk_product_repository_product_id',
        'product_repository',
        type_='foreignkey',
    )
    op.drop_index('ix_products_is_archived', table_name='products')
    op.drop_table('products')
