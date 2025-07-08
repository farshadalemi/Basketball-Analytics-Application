"""
Analysis Job schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AnalysisJobBase(BaseModel):
    """Base analysis job schema"""
    job_id: str
    video_id: int
    status: Optional[str] = "pending"
    progress: Optional[int] = 0
    message: Optional[str] = None
    error_message: Optional[str] = None
    analysis_options: Optional[str] = None
    result_url: Optional[str] = None
    download_url: Optional[str] = None


class AnalysisJobCreate(AnalysisJobBase):
    """Schema for creating analysis job"""
    pass


class AnalysisJobUpdate(BaseModel):
    """Schema for updating analysis job"""
    status: Optional[str] = None
    progress: Optional[int] = None
    message: Optional[str] = None
    error_message: Optional[str] = None
    result_url: Optional[str] = None
    download_url: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AnalysisJobInDB(AnalysisJobBase):
    """Schema for analysis job in database"""
    id: int
    user_id: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalysisJobSchema(AnalysisJobInDB):
    """Public analysis job schema"""
    pass
