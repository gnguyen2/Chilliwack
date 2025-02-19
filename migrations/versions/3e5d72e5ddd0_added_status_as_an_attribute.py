"""added status as an attribute

Revision ID: 3e5d72e5ddd0
Revises: 312eac92f1c9
Create Date: 2025-02-18 23:10:28.715065

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e5d72e5ddd0'
down_revision = '312eac92f1c9'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add column with default value
    op.add_column('user', sa.Column('status', sa.String(length=20), nullable=False, server_default='active'))

    # Step 2: Drop profile_picture column separately
    op.drop_column('user', 'profile_picture')


def downgrade():
    # Step 1: Re-add profile_picture column
    op.add_column('user', sa.Column('profile_picture', sa.String(length=200), nullable=True))

    # Step 2: Remove status column
    op.drop_column('user', 'status')
