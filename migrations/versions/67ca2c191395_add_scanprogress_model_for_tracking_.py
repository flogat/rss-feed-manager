"""Add ScanProgress model for tracking feed updates

Revision ID: 67ca2c191395
Revises: 31ed322d07ad
Create Date: 2025-01-13 15:54:32.249254

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67ca2c191395'
down_revision = '31ed322d07ad'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('scan_progress',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('is_scanning', sa.Boolean(), nullable=True),
    sa.Column('current_feed', sa.String(length=500), nullable=True),
    sa.Column('current_index', sa.Integer(), nullable=True),
    sa.Column('total_feeds', sa.Integer(), nullable=True),
    sa.Column('completed', sa.Boolean(), nullable=True),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('scan_progress')
    # ### end Alembic commands ###
