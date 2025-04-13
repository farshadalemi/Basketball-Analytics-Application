"""Create report tables

Revision ID: 001
Revises: 
Create Date: 2023-04-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create reports table
    op.create_table(
        'report',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('video_title', sa.String(), nullable=True),
        sa.Column('team_name', sa.String(), nullable=True),
        sa.Column('opponent_name', sa.String(), nullable=True),
        sa.Column('game_date', sa.DateTime(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('analysis_results', JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_id'), 'report', ['id'], unique=False)
    op.create_index(op.f('ix_report_title'), 'report', ['title'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_report_title'), table_name='report')
    op.drop_index(op.f('ix_report_id'), table_name='report')
    op.drop_table('report')
