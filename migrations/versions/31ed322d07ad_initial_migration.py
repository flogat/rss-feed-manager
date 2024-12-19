"""Initial migration

Revision ID: 31ed322d07ad
Revises: 
Create Date: 2024-12-19 14:17:05.657557

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31ed322d07ad'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=False),
    sa.Column('password_hash', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('rss_feed',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=True),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('error_count', sa.Integer(), nullable=True),
    sa.Column('last_error', sa.String(length=500), nullable=True),
    sa.Column('num_articles', sa.Integer(), nullable=True),
    sa.Column('last_article_date', sa.DateTime(), nullable=True),
    sa.Column('last_scan_trigger', sa.String(length=50), nullable=True),
    sa.Column('last_scan_time', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('url')
    )
    op.create_table('article',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('feed_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('link', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('published_date', sa.DateTime(), nullable=True),
    sa.Column('collected_date', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['feed_id'], ['rss_feed.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('link')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('article')
    op.drop_table('rss_feed')
    op.drop_table('admin')
    # ### end Alembic commands ###
