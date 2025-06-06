"""empty message

Revision ID: 2f6fb5f0a049
Revises: e806a3e563e1
Create Date: 2025-04-17 22:06:05.743560

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f6fb5f0a049'
down_revision = 'e806a3e563e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('department', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(length=100, collation='SQL_Latin1_General_CP1_CI_AS'),
               nullable=False)

    with op.batch_alter_table('general_petition', schema=None) as batch_op:
        batch_op.add_column(sa.Column('request_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'request', ['request_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('general_petition', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('request_id')

    with op.batch_alter_table('department', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(length=100, collation='SQL_Latin1_General_CP1_CI_AS'),
               nullable=True)

    # ### end Alembic commands ###
