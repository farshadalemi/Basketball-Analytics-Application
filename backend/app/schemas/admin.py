"""Admin schemas for system management."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class UserStatsItem(BaseModel):
    """User statistics item."""
    id: int
    username: str
    email: str
    video_count: int


class UserStats(BaseModel):
    """User statistics."""
    total_users: int
    active_users: int
    inactive_users: int
    admin_users: int
    regular_users: int
    top_users_by_content: List[UserStatsItem]


class VideoStats(BaseModel):
    """Video statistics."""
    total_videos: int
    processing_videos: int
    completed_videos: int
    failed_videos: int


class StorageStatsItem(BaseModel):
    """Storage statistics item."""
    id: int
    username: str
    email: str
    video_count: int
    storage_used_mb: float


class StorageStats(BaseModel):
    """Storage statistics."""
    total_storage_mb: float
    total_videos: int
    avg_video_size_mb: float
    top_storage_users: List[StorageStatsItem]


class StorageStatsBase(BaseModel):
    """Base storage statistics."""
    total_storage_mb: float
    avg_storage_per_user_mb: float


class SystemStats(BaseModel):
    """System statistics."""
    user_stats: Dict[str, int]
    video_stats: Dict[str, int]
    storage_stats: Dict[str, float]
