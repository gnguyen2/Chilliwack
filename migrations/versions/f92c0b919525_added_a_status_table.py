from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f92c0b919525'
down_revision = '3e5d72e5ddd0'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the default constraint on the 'status' column
    op.execute("""
        DECLARE @constraint_name NVARCHAR(200)
        SELECT @constraint_name = name
        FROM sys.default_constraints
        WHERE parent_object_id = OBJECT_ID('user')
        AND type = 'D'
        AND parent_column_id = (
            SELECT column_id
            FROM sys.columns
            WHERE object_id = OBJECT_ID('user')
            AND name = 'status'
        )
        IF @constraint_name IS NOT NULL
        BEGIN
            EXEC('ALTER TABLE [user] DROP CONSTRAINT ' + @constraint_name)
        END
    """)

    # Add the new 'status_id' column and foreign key
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_user_status', 'status', ['status_id'], ['id'])
        batch_op.drop_column('status')


def downgrade():
    # Revert the changes
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.VARCHAR(length=20, collation='SQL_Latin1_General_CP1_CI_AS'), server_default=sa.text("('active')"), nullable=False))
        batch_op.drop_constraint('fk_user_status', type_='foreignkey')
        batch_op.drop_column('status_id')

    # Re-add the default constraint to the 'status' column
    op.execute("ALTER TABLE [user] ADD CONSTRAINT DF_user_status DEFAULT 'active' FOR status")