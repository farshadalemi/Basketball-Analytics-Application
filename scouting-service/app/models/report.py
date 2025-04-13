"""Report model for storing scouting reports."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.sql import func

from app.db.base_class import Base


class Report(Base):
    """Report model for storing scouting reports."""
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    
    # Video information
    video_id = Column(Integer, nullable=False)  # Reference to the video in the main service
    video_title = Column(String, nullable=True)
    
    # Report information
    team_name = Column(String, nullable=True)
    opponent_name = Column(String, nullable=True)
    game_date = Column(DateTime, nullable=True)
    
    # Report file
    file_path = Column(String, nullable=True)  # Path to the PDF in MinIO
    
    # Processing status
    status = Column(String, default="queued")  # "queued", "processing", "completed", "failed"
    
    # Analysis results
    analysis_results = Column(JSON, nullable=True)  # Store analysis results as JSON
    
    # User information
    user_id = Column(Integer, nullable=False)  # Reference to the user in the main service
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
