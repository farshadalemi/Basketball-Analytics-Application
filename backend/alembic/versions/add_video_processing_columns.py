"""Add video processing columns

Revision ID: add_video_processing_columns
Revises: create_base_tables
Create Date: 2025-04-03 16:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_video_processing_columns'
down_revision = 'create_base_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add processing_status column
    op.add_column('videos', sa.Column('processing_status', sa.String(), nullable=True, server_default='queued'))

    # Add duration column
    op.add_column('videos', sa.Column('duration', sa.Integer(), nullable=True))

    # Add thumbnail_url column
    op.add_column('videos', sa.Column('thumbnail_url', sa.String(), nullable=True))

    # Add processed_at column
    op.add_column('videos', sa.Column('processed_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove columns in reverse order
    op.drop_column('videos', 'processed_at')
    op.drop_column('videos', 'thumbnail_url')
    op.drop_column('videos', 'duration')
    op.drop_column('videos', 'processing_status')
