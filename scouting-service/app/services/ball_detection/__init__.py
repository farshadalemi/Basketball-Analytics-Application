"""
Ball Detection Feature Module.

This module provides ball detection and shot analysis capabilities including:
- Ball detection and tracking algorithms
- Shot detection and analysis
- Basketball-specific trajectory analysis
"""

from .detectors.ball_detector import BallDetector
from .analysis.shot_detection import ShotDetector

__all__ = [
    "BallDetector",
    "ShotDetector"
]
