"""Add article fields for summary, seo, publishing, and featured image

Revision ID: 31e03485e9a1
Revises: b2aab1c6a41c
Create Date: 2025-06-18 10:47:02.691175

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31e03485e9a1'
down_revision = 'b2aab1c6a41c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('summary', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('is_published', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('published_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('allow_comments', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('meta_title', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('meta_description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('meta_keywords', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('canonical_url', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('featured_image', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('ext_json', sa.Text(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.drop_column('ext_json')
        batch_op.drop_column('featured_image')
        batch_op.drop_column('canonical_url')
        batch_op.drop_column('meta_keywords')
        batch_op.drop_column('meta_description')
        batch_op.drop_column('meta_title')
        batch_op.drop_column('allow_comments')
        batch_op.drop_column('published_at')
        batch_op.drop_column('is_published')
        batch_op.drop_column('summary')

    # ### end Alembic commands ###
