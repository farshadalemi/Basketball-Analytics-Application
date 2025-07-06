"""
Video Processing Feature Module.

This module provides video processing capabilities including:
- Video processing and analysis
- Job management for long-running video tasks
- Performance monitoring and optimization
"""

from .processors.video_processor import VideoProcessor, VideoProcessingConfig
from .management.job_manager import VideoProcessingJobManager, get_job_manager, start_job_manager, stop_job_manager

__all__ = [
    "VideoProcessor",
    "VideoProcessingConfig", 
    "VideoProcessingJobManager",
    "get_job_manager",
    "start_job_manager",
    "stop_job_manager"
]
