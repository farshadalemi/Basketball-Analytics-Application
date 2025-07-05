"""Add computer vision models

Revision ID: 002
Revises: 001
Create Date: 2025-07-04 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create videoprocessingjob table
    op.create_table(
        'videoprocessingjob',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('processing_config', JSON(), nullable=True),
        sa.Column('total_frames', sa.Integer(), nullable=True),
        sa.Column('processed_frames', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['report_id'], ['report.id'], )
    )
    op.create_index(op.f('ix_videoprocessingjob_id'), 'videoprocessingjob', ['id'], unique=False)
    op.create_index(op.f('ix_videoprocessingjob_video_id'), 'videoprocessingjob', ['video_id'], unique=False)

    # Create courtdetection table
    op.create_table(
        'courtdetection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('frame_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('court_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('court_corners', JSON(), nullable=True),
        sa.Column('three_point_line', JSON(), nullable=True),
        sa.Column('free_throw_line', JSON(), nullable=True),
        sa.Column('center_circle', JSON(), nullable=True),
        sa.Column('paint_area', JSON(), nullable=True),
        sa.Column('homography_matrix', JSON(), nullable=True),
        sa.Column('court_width_pixels', sa.Float(), nullable=True),
        sa.Column('court_height_pixels', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['videoprocessingjob.id'], )
    )
    op.create_index(op.f('ix_courtdetection_id'), 'courtdetection', ['id'], unique=False)

    # Create playerdetection table
    op.create_table(
        'playerdetection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('frame_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('player_id', sa.String(), nullable=False),
        sa.Column('jersey_number', sa.String(), nullable=True),
        sa.Column('team_id', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('bbox_x1', sa.Float(), nullable=False),
        sa.Column('bbox_y1', sa.Float(), nullable=False),
        sa.Column('bbox_x2', sa.Float(), nullable=False),
        sa.Column('bbox_y2', sa.Float(), nullable=False),
        sa.Column('court_x', sa.Float(), nullable=True),
        sa.Column('court_y', sa.Float(), nullable=True),
        sa.Column('is_on_court', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('pose_keypoints', JSON(), nullable=True),
        sa.Column('pose_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['videoprocessingjob.id'], )
    )
    op.create_index(op.f('ix_playerdetection_id'), 'playerdetection', ['id'], unique=False)

    # Create teamclassification table
    op.create_table(
        'teamclassification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('frame_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('team_a_players', JSON(), nullable=True),
        sa.Column('team_b_players', JSON(), nullable=True),
        sa.Column('team_a_primary_color', JSON(), nullable=True),
        sa.Column('team_a_secondary_color', JSON(), nullable=True),
        sa.Column('team_b_primary_color', JSON(), nullable=True),
        sa.Column('team_b_secondary_color', JSON(), nullable=True),
        sa.Column('classification_confidence', sa.Float(), nullable=True),
        sa.Column('team_a_formation', sa.String(), nullable=True),
        sa.Column('team_b_formation', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['videoprocessingjob.id'], )
    )
    op.create_index(op.f('ix_teamclassification_id'), 'teamclassification', ['id'], unique=False)

    # Create balldetection table
    op.create_table(
        'balldetection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('frame_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('ball_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('ball_x', sa.Float(), nullable=True),
        sa.Column('ball_y', sa.Float(), nullable=True),
        sa.Column('court_x', sa.Float(), nullable=True),
        sa.Column('court_y', sa.Float(), nullable=True),
        sa.Column('ball_height', sa.Float(), nullable=True),
        sa.Column('ball_velocity', JSON(), nullable=True),
        sa.Column('possessing_player_id', sa.String(), nullable=True),
        sa.Column('possessing_team', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['videoprocessingjob.id'], )
    )
    op.create_index(op.f('ix_balldetection_id'), 'balldetection', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_balldetection_id'), table_name='balldetection')
    op.drop_table('balldetection')
    op.drop_index(op.f('ix_teamclassification_id'), table_name='teamclassification')
    op.drop_table('teamclassification')
    op.drop_index(op.f('ix_playerdetection_id'), table_name='playerdetection')
    op.drop_table('playerdetection')
    op.drop_index(op.f('ix_courtdetection_id'), table_name='courtdetection')
    op.drop_table('courtdetection')
    op.drop_index(op.f('ix_videoprocessingjob_video_id'), table_name='videoprocessingjob')
    op.drop_index(op.f('ix_videoprocessingjob_id'), table_name='videoprocessingjob')
    op.drop_table('videoprocessingjob')
