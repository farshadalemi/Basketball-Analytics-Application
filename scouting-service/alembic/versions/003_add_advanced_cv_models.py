"""Add advanced computer vision models

Revision ID: 003
Revises: 002
Create Date: 2025-07-04 20:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create formationanalysis table
    op.create_table(
        'formationanalysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('frame_number', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('offensive_team', sa.String(), nullable=True),
        sa.Column('defensive_team', sa.String(), nullable=True),
        sa.Column('offensive_formation', sa.String(), nullable=True),
        sa.Column('offensive_confidence', sa.Float(), nullable=True),
        sa.Column('defensive_formation', sa.String(), nullable=True),
        sa.Column('defensive_confidence', sa.Float(), nullable=True),
        sa.Column('team_spacing', JSON(), nullable=True),
        sa.Column('court_coverage', JSON(), nullable=True),
        sa.Column('ball_screen_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pick_and_roll_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('fast_break_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['videoprocessingjob.id'], )
    )
    op.create_index(op.f('ix_formationanalysis_id'), 'formationanalysis', ['id'], unique=False)

    # Create playanalysis table
    op.create_table(
        'playanalysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('start_frame', sa.Integer(), nullable=False),
        sa.Column('end_frame', sa.Integer(), nullable=False),
        sa.Column('start_timestamp', sa.Float(), nullable=False),
        sa.Column('end_timestamp', sa.Float(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=False),
        sa.Column('play_type', sa.String(), nullable=True),
        sa.Column('play_subtype', sa.String(), nullable=True),
        sa.Column('play_confidence', sa.Float(), nullable=True),
        sa.Column('primary_player_id', sa.String(), nullable=True),
        sa.Column('secondary_players', JSON(), nullable=True),
        sa.Column('successful', sa.Boolean(), nullable=True),
        sa.Column('points_scored', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('play_location', JSON(), nullable=True),
        sa.Column('player_movements', JSON(), nullable=True),
        sa.Column('play_efficiency', sa.Float(), nullable=True),
        sa.Column('defensive_pressure', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['videoprocessingjob.id'], )
    )
    op.create_index(op.f('ix_playanalysis_id'), 'playanalysis', ['id'], unique=False)

    # Create gamestatistics table
    op.create_table(
        'gamestatistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('total_duration', sa.Float(), nullable=True),
        sa.Column('team_a_stats', JSON(), nullable=True),
        sa.Column('team_b_stats', JSON(), nullable=True),
        sa.Column('player_stats', JSON(), nullable=True),
        sa.Column('pace_of_play', sa.Float(), nullable=True),
        sa.Column('ball_possession_time', JSON(), nullable=True),
        sa.Column('shot_chart', JSON(), nullable=True),
        sa.Column('player_heat_maps', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['job_id'], ['videoprocessingjob.id'], )
    )
    op.create_index(op.f('ix_gamestatistics_id'), 'gamestatistics', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_gamestatistics_id'), table_name='gamestatistics')
    op.drop_table('gamestatistics')
    op.drop_index(op.f('ix_playanalysis_id'), table_name='playanalysis')
    op.drop_table('playanalysis')
    op.drop_index(op.f('ix_formationanalysis_id'), table_name='formationanalysis')
    op.drop_table('formationanalysis')
