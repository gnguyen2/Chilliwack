"""Merge all heads

Revision ID: e806a3e563e1
Revises: 0d377d363154, 1d2157266c6f
Create Date: 2025-04-17 21:53:20.974172

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e806a3e563e1'
down_revision = ('0d377d363154', '1d2157266c6f')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
