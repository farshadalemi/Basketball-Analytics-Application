from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class VideoBase(BaseModel):
    """Base Video schema."""

    title: str
    description: Optional[str] = None


class VideoCreate(VideoBase):
    """Video creation schema."""

    file_path: str
    content_type: str


class VideoUpdate(BaseModel):
    """Video update schema."""

    title: Optional[str] = None
    description: Optional[str] = None
    processing_status: Optional[str] = None  # "queued", "processing", "completed", "failed"
    duration: Optional[int] = None  # Duration in seconds
    thumbnail_url: Optional[str] = None
    processed_at: Optional[datetime] = None


class VideoInDBBase(VideoBase):
    """Base Video in DB schema."""

    id: int
    user_id: int
    file_path: str
    content_type: str
    created_at: datetime
    processing_status: Optional[str] = "queued"  # Default status
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Video(VideoInDBBase):
    """Video schema with streaming URL."""

    streaming_url: Optional[str] = None

class VideoInDB(VideoInDBBase):
    pass 