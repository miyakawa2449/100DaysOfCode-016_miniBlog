"""Add user profile and SNS fields

Revision ID: b2aab1c6a41c
Revises: 8263ea2ff740
Create Date: 2025-06-18 06:57:03.625633

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2aab1c6a41c'
down_revision = '8263ea2ff740'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sns_x', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('sns_facebook', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('sns_instagram', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('sns_threads', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('sns_youtube', sa.String(length=100), nullable=True))
        batch_op.drop_column('sns_accounts')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sns_accounts', sa.TEXT(), nullable=True))
        batch_op.drop_column('sns_youtube')
        batch_op.drop_column('sns_threads')
        batch_op.drop_column('sns_instagram')
        batch_op.drop_column('sns_facebook')
        batch_op.drop_column('sns_x')

    # ### end Alembic commands ###
