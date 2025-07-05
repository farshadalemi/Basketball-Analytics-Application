"""Computer vision models for storing basketball analytics data."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class VideoProcessingJob(Base):
    """Model for tracking video processing jobs."""
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, nullable=False, index=True)  # Reference to video in main service
    report_id = Column(Integer, ForeignKey("report.id"), nullable=True)  # Link to report
    
    # Job information
    status = Column(String, default="queued")  # "queued", "processing", "completed", "failed"
    progress = Column(Float, default=0.0)  # Progress percentage (0.0 to 100.0)
    
    # Processing configuration
    processing_config = Column(JSON, nullable=True)  # Configuration parameters
    
    # Results summary
    total_frames = Column(Integer, nullable=True)
    processed_frames = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CourtDetection(Base):
    """Model for storing court detection results."""
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("videoprocessingjob.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)  # Timestamp in seconds
    
    # Court detection results
    court_detected = Column(Boolean, default=False)
    confidence_score = Column(Float, nullable=True)
    
    # Court boundaries (normalized coordinates 0-1)
    court_corners = Column(JSON, nullable=True)  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    
    # Court features
    three_point_line = Column(JSON, nullable=True)  # Array of points
    free_throw_line = Column(JSON, nullable=True)  # Array of points
    center_circle = Column(JSON, nullable=True)  # Center and radius
    paint_area = Column(JSON, nullable=True)  # Polygon points
    
    # Homography matrix for perspective transformation
    homography_matrix = Column(JSON, nullable=True)  # 3x3 transformation matrix
    
    # Court dimensions in real-world units
    court_width_pixels = Column(Float, nullable=True)
    court_height_pixels = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=func.now())


class PlayerDetection(Base):
    """Model for storing player detection and tracking results."""
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("videoprocessingjob.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    
    # Player identification
    player_id = Column(String, nullable=False)  # Unique tracking ID
    jersey_number = Column(String, nullable=True)  # Detected jersey number
    team_id = Column(String, nullable=True)  # "team_a" or "team_b"
    
    # Detection results
    confidence_score = Column(Float, nullable=False)
    
    # Bounding box (normalized coordinates 0-1)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    
    # Player position on court (real-world coordinates)
    court_x = Column(Float, nullable=True)  # X position on court
    court_y = Column(Float, nullable=True)  # Y position on court
    
    # Player state
    is_on_court = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)  # Is player actively playing
    
    # Pose estimation data
    pose_keypoints = Column(JSON, nullable=True)  # MediaPipe pose keypoints
    pose_confidence = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=func.now())


class TeamClassification(Base):
    """Model for storing team classification results."""
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("videoprocessingjob.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    
    # Team information
    team_a_players = Column(JSON, nullable=True)  # List of player IDs
    team_b_players = Column(JSON, nullable=True)  # List of player IDs
    
    # Color analysis
    team_a_primary_color = Column(JSON, nullable=True)  # RGB values
    team_a_secondary_color = Column(JSON, nullable=True)
    team_b_primary_color = Column(JSON, nullable=True)
    team_b_secondary_color = Column(JSON, nullable=True)
    
    # Classification confidence
    classification_confidence = Column(Float, nullable=True)
    
    # Team formation
    team_a_formation = Column(String, nullable=True)  # "offense", "defense", "transition"
    team_b_formation = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=func.now())


class BallDetection(Base):
    """Model for storing basketball detection and tracking results."""
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("videoprocessingjob.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    
    # Ball detection
    ball_detected = Column(Boolean, default=False)
    confidence_score = Column(Float, nullable=True)
    
    # Ball position (normalized coordinates 0-1)
    ball_x = Column(Float, nullable=True)
    ball_y = Column(Float, nullable=True)
    
    # Ball position on court (real-world coordinates)
    court_x = Column(Float, nullable=True)
    court_y = Column(Float, nullable=True)
    
    # Ball state
    ball_height = Column(Float, nullable=True)  # Estimated height above court
    ball_velocity = Column(JSON, nullable=True)  # [vx, vy] velocity vector
    
    # Possession information
    possessing_player_id = Column(String, nullable=True)
    possessing_team = Column(String, nullable=True)  # "team_a" or "team_b"
    
    created_at = Column(DateTime, default=func.now())


class FormationAnalysis(Base):
    """Model for storing team formation and tactical analysis."""
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("videoprocessingjob.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=False)
    
    # Formation type
    offensive_team = Column(String, nullable=True)  # "team_a" or "team_b"
    defensive_team = Column(String, nullable=True)
    
    # Offensive formation
    offensive_formation = Column(String, nullable=True)  # "motion", "pick_and_roll", "isolation", etc.
    offensive_confidence = Column(Float, nullable=True)
    
    # Defensive formation
    defensive_formation = Column(String, nullable=True)  # "man_to_man", "zone_2_3", "zone_3_2", "press", etc.
    defensive_confidence = Column(Float, nullable=True)
    
    # Spatial analysis
    team_spacing = Column(JSON, nullable=True)  # Spacing metrics for both teams
    court_coverage = Column(JSON, nullable=True)  # Court area coverage
    
    # Tactical insights
    ball_screen_detected = Column(Boolean, default=False)
    pick_and_roll_detected = Column(Boolean, default=False)
    fast_break_detected = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())


class PlayAnalysis(Base):
    """Model for storing individual play analysis and classification."""
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("videoprocessingjob.id"), nullable=False)
    
    # Play timing
    start_frame = Column(Integer, nullable=False)
    end_frame = Column(Integer, nullable=False)
    start_timestamp = Column(Float, nullable=False)
    end_timestamp = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)  # Duration in seconds
    
    # Play classification
    play_type = Column(String, nullable=True)  # "shot", "pass", "dribble", "rebound", "turnover", etc.
    play_subtype = Column(String, nullable=True)  # "three_pointer", "layup", "dunk", etc.
    play_confidence = Column(Float, nullable=True)
    
    # Players involved
    primary_player_id = Column(String, nullable=True)  # Main player in the play
    secondary_players = Column(JSON, nullable=True)  # Other players involved
    
    # Play outcome
    successful = Column(Boolean, nullable=True)
    points_scored = Column(Integer, default=0)
    
    # Spatial data
    play_location = Column(JSON, nullable=True)  # Court coordinates where play occurred
    player_movements = Column(JSON, nullable=True)  # Movement trajectories
    
    # Advanced metrics
    play_efficiency = Column(Float, nullable=True)
    defensive_pressure = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=func.now())


class GameStatistics(Base):
    """Model for storing aggregated game statistics."""
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("videoprocessingjob.id"), nullable=False)
    
    # Game information
    total_duration = Column(Float, nullable=True)  # Total game duration in seconds
    
    # Team statistics
    team_a_stats = Column(JSON, nullable=True)  # Comprehensive team A statistics
    team_b_stats = Column(JSON, nullable=True)  # Comprehensive team B statistics
    
    # Player statistics
    player_stats = Column(JSON, nullable=True)  # Individual player statistics
    
    # Advanced analytics
    pace_of_play = Column(Float, nullable=True)
    ball_possession_time = Column(JSON, nullable=True)  # Possession time per team
    
    # Heat maps and spatial data
    shot_chart = Column(JSON, nullable=True)  # Shot locations and outcomes
    player_heat_maps = Column(JSON, nullable=True)  # Player movement heat maps
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
