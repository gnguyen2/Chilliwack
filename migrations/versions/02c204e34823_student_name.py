"""student name

Revision ID: 02c204e34823
Revises: a368dec6b45d
Create Date: 2025-04-21 22:13:54.402697

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '02c204e34823'
down_revision = 'a368dec6b45d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ca_responses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('student_name', sa.String(length=255), nullable=False))
        batch_op.drop_column('user_name')

    with op.batch_alter_table('general_petition', schema=None) as batch_op:
        batch_op.add_column(sa.Column('student_name', sa.String(length=100), nullable=True))
        batch_op.drop_column('student_first_name')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('general_petition', schema=None) as batch_op:
        batch_op.add_column(sa.Column('student_first_name', sa.VARCHAR(length=100, collation='SQL_Latin1_General_CP1_CI_AS'), autoincrement=False, nullable=True))
        batch_op.drop_column('student_name')

    with op.batch_alter_table('ca_responses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_name', sa.VARCHAR(length=255, collation='SQL_Latin1_General_CP1_CI_AS'), autoincrement=False, nullable=False))
        batch_op.drop_column('student_name')

    # ### end Alembic commands ###
