"""
Basketball Analytics Services Package.

This package contains all the service modules for basketball analytics:
- court_detection: Court detection and analysis
- player_tracking: Player detection, tracking, and analysis
- ball_detection: Ball detection and shot analysis
- video_processing: Video processing and job management
- analytics: Analytics services and report generation
"""

# Import main service modules for easy access
from . import court_detection
from . import player_tracking
from . import ball_detection
from . import video_processing
from . import analytics

__all__ = [
    "court_detection",
    "player_tracking",
    "ball_detection",
    "video_processing",
    "analytics"
]
