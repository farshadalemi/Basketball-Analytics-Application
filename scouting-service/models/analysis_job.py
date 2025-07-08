"""
Analysis Job database model
"""
from enum import Enum
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel
import uuid

from .database import Base

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AnalysisJobDB(Base):
    """Database model for analysis jobs"""
    __tablename__ = "analysis_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(Integer, index=True)
    video_path = Column(String, nullable=False)
    status = Column(String, default=JobStatus.PENDING)
    progress = Column(Integer, default=0)
    message = Column(String, default="")
    error = Column(Text, nullable=True)
    result_path = Column(String, nullable=True)
    metadata_path = Column(String, nullable=True)
    analysis_options = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class AnalysisJob(BaseModel):
    """Pydantic model for analysis jobs"""
    job_id: str
    video_id: int
    video_path: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = ""
    error: Optional[str] = None
    result_path: Optional[str] = None
    metadata_path: Optional[str] = None
    analysis_options: Dict = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
