"""
Comprehensive video processing pipeline for basketball analytics.

This module provides a complete video processing pipeline that orchestrates:
- Court detection
- Player detection and tracking
- Team classification
- Ball detection and tracking
- Formation analysis
- Play detection and classification
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, AsyncGenerator
import logging
import asyncio
from dataclasses import dataclass, asdict
import json
from datetime import datetime
import tempfile
import os

from app.services.court_detection import SimplifiedCourtDetector
from app.services.court_detection.detectors.simplified_court_detector import SimplifiedCourtFeatures
from app.services.player_tracking import PlayerDetector
from app.services.player_tracking.detectors.player_detector import PlayerDetection
from app.services.player_tracking import TeamClassifier
from app.services.player_tracking.classification.team_classifier import TeamClassification
from app.services.ball_detection import BallDetector
from app.services.ball_detection.detectors.ball_detector import BallDetection

logger = logging.getLogger(__name__)


@dataclass
class FrameAnalysis:
    """Data class for storing complete frame analysis results."""
    frame_number: int
    timestamp: float
    court_features: Optional[SimplifiedCourtFeatures] = None
    player_detections: List[PlayerDetection] = None
    team_classification: Optional[TeamClassification] = None
    ball_detection: Optional[BallDetection] = None
    processing_time: float = 0.0


@dataclass
class VideoProcessingConfig:
    """Configuration for video processing pipeline."""
    # Processing parameters
    process_every_nth_frame: int = 1  # Process every frame by default
    max_frames: Optional[int] = None  # Limit processing to N frames
    
    # Detection thresholds
    court_detection_confidence: float = 0.7
    player_detection_confidence: float = 0.5
    ball_detection_confidence: float = 0.3
    
    # Processing options
    enable_court_detection: bool = True
    enable_player_detection: bool = True
    enable_team_classification: bool = True
    enable_ball_detection: bool = True
    enable_pose_estimation: bool = False  # Computationally expensive
    enable_jersey_ocr: bool = False  # Computationally expensive
    
    # Output options
    save_annotated_frames: bool = False
    output_video_path: Optional[str] = None


class VideoProcessor:
    """
    Comprehensive video processing pipeline for basketball analytics.
    
    This class orchestrates all computer vision components to provide
    complete basketball game analysis from video input.
    """
    
    def __init__(self, config: Optional[VideoProcessingConfig] = None):
        """
        Initialize the video processor.
        
        Args:
            config: Video processing configuration
        """
        self.config = config or VideoProcessingConfig()
        
        # Initialize computer vision components
        self.court_detector = SimplifiedCourtDetector() if self.config.enable_court_detection else None
        self.player_detector = PlayerDetector() if self.config.enable_player_detection else None
        self.team_classifier = TeamClassifier() if self.config.enable_team_classification else None
        self.ball_detector = BallDetector() if self.config.enable_ball_detection else None
        
        # Processing state
        self.current_homography = None
        self.frame_analyses = []
        self.processing_stats = {
            'total_frames': 0,
            'processed_frames': 0,
            'average_processing_time': 0.0,
            'total_processing_time': 0.0
        }
        
        logger.info("VideoProcessor initialized successfully")
    
    async def process_video_file(self, video_path: str, 
                                progress_callback: Optional[callable] = None) -> List[FrameAnalysis]:
        """
        Process a video file and return analysis results.
        
        Args:
            video_path: Path to the video file
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of frame analysis results
        """
        try:
            logger.info(f"Starting video processing: {video_path}")
            
            # Open video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            self.processing_stats['total_frames'] = total_frames
            
            # Limit frames if specified
            if self.config.max_frames:
                total_frames = min(total_frames, self.config.max_frames)
            
            logger.info(f"Video properties: {total_frames} frames, {fps} FPS")
            
            # Process frames
            frame_number = 0
            processed_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret or (self.config.max_frames and frame_number >= self.config.max_frames):
                    break
                
                # Process frame if it matches the sampling rate
                if frame_number % self.config.process_every_nth_frame == 0:
                    timestamp = frame_number / fps
                    
                    # Process the frame
                    analysis = await self._process_frame(frame, frame_number, timestamp)
                    self.frame_analyses.append(analysis)
                    
                    processed_count += 1
                    self.processing_stats['processed_frames'] = processed_count
                    
                    # Update progress
                    if progress_callback:
                        progress = (frame_number + 1) / total_frames * 100
                        await progress_callback(progress, analysis)
                    
                    # Yield control to allow other tasks
                    await asyncio.sleep(0)
                
                frame_number += 1
            
            cap.release()
            
            # Calculate final statistics
            self._calculate_final_stats()
            
            logger.info(f"Video processing completed: {processed_count} frames processed")
            return self.frame_analyses
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise
    
    async def _process_frame(self, frame: np.ndarray, frame_number: int, 
                           timestamp: float) -> FrameAnalysis:
        """
        Process a single video frame.
        
        Args:
            frame: Video frame
            frame_number: Frame number
            timestamp: Timestamp in seconds
            
        Returns:
            FrameAnalysis object with results
        """
        start_time = datetime.now()
        
        try:
            analysis = FrameAnalysis(
                frame_number=frame_number,
                timestamp=timestamp,
                player_detections=[]
            )
            
            # 1. Court detection (if enabled and not already established)
            if self.court_detector and (self.current_homography is None or frame_number % 30 == 0):
                court_features = self.court_detector.detect_court(frame)
                analysis.court_features = court_features
                
                if (court_features.confidence_score >= self.config.court_detection_confidence and 
                    court_features.homography_matrix is not None):
                    self.current_homography = court_features.homography_matrix
                    
                    # Update other detectors with homography
                    if self.player_detector:
                        self.player_detector.set_court_homography(self.current_homography)
                    if self.ball_detector:
                        self.ball_detector.set_court_homography(self.current_homography)
            
            # 2. Player detection (if enabled)
            if self.player_detector:
                player_detections = self.player_detector.detect_players(frame, frame_number)
                analysis.player_detections = player_detections
                
                # Transform player positions to court coordinates
                for player in player_detections:
                    if self.current_homography is not None:
                        court_pos = self.player_detector.transform_to_court_coordinates(player.bbox)
                        player.court_position = court_pos
            
            # 3. Team classification (if enabled and we have enough players)
            if (self.team_classifier and analysis.player_detections and 
                len(analysis.player_detections) >= 4):
                
                # Convert player detections to format expected by team classifier
                player_data = []
                for player in analysis.player_detections:
                    player_data.append({
                        'player_id': player.player_id,
                        'bbox': player.bbox
                    })
                
                team_classification = self.team_classifier.classify_teams(frame, player_data)
                analysis.team_classification = team_classification
                
                # Update player team assignments
                for player in analysis.player_detections:
                    if player.player_id in team_classification.team_a_players:
                        player.team_id = 'team_a'
                    elif player.player_id in team_classification.team_b_players:
                        player.team_id = 'team_b'
            
            # 4. Ball detection (if enabled)
            if self.ball_detector:
                ball_detection = self.ball_detector.detect_ball(frame, frame_number)
                
                # Analyze ball possession if we have player detections
                if ball_detection.detected and analysis.player_detections:
                    player_data = []
                    for player in analysis.player_detections:
                        player_data.append({
                            'player_id': player.player_id,
                            'bbox': player.bbox,
                            'team_id': player.team_id
                        })
                    
                    ball_detection = self.ball_detector.analyze_possession(ball_detection, player_data)
                
                analysis.ball_detection = ball_detection
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            analysis.processing_time = processing_time
            
            # Update statistics
            self.processing_stats['total_processing_time'] += processing_time
            
            logger.debug(f"Frame {frame_number} processed in {processing_time:.3f}s")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error processing frame {frame_number}: {str(e)}")
            # Return empty analysis on error
            return FrameAnalysis(
                frame_number=frame_number,
                timestamp=timestamp,
                player_detections=[],
                processing_time=0.0
            )
    
    def _calculate_final_stats(self):
        """Calculate final processing statistics."""
        if self.processing_stats['processed_frames'] > 0:
            self.processing_stats['average_processing_time'] = (
                self.processing_stats['total_processing_time'] / 
                self.processing_stats['processed_frames']
            )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return self.processing_stats.copy()
    
    def export_analysis_to_json(self, output_path: str):
        """
        Export analysis results to JSON file.
        
        Args:
            output_path: Path to output JSON file
        """
        try:
            # Convert analysis results to serializable format
            export_data = {
                'processing_stats': self.processing_stats,
                'config': asdict(self.config),
                'frame_analyses': []
            }
            
            for analysis in self.frame_analyses:
                frame_data = {
                    'frame_number': analysis.frame_number,
                    'timestamp': analysis.timestamp,
                    'processing_time': analysis.processing_time,
                    'court_features': self._serialize_court_features(analysis.court_features),
                    'player_detections': self._serialize_player_detections(analysis.player_detections),
                    'team_classification': self._serialize_team_classification(analysis.team_classification),
                    'ball_detection': self._serialize_ball_detection(analysis.ball_detection)
                }
                export_data['frame_analyses'].append(frame_data)
            
            # Write to file
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Analysis exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting analysis: {str(e)}")
            raise

    def _serialize_court_features(self, court_features: Optional[SimplifiedCourtFeatures]) -> Optional[Dict[str, Any]]:
        """Serialize court features to dictionary."""
        if court_features is None:
            return None

        return {
            'corners': court_features.corners,
            'three_point_line': court_features.three_point_line,
            'free_throw_line': court_features.free_throw_line,
            'center_circle': court_features.center_circle,
            'paint_area': court_features.paint_area,
            'homography_matrix': court_features.homography_matrix.tolist() if court_features.homography_matrix is not None else None,
            'confidence_score': court_features.confidence_score
        }

    def _serialize_player_detections(self, player_detections: List[PlayerDetection]) -> List[Dict[str, Any]]:
        """Serialize player detections to list of dictionaries."""
        if not player_detections:
            return []

        serialized = []
        for player in player_detections:
            player_data = {
                'player_id': player.player_id,
                'bbox': player.bbox,
                'confidence': player.confidence,
                'jersey_number': player.jersey_number,
                'team_id': player.team_id,
                'pose_keypoints': player.pose_keypoints,
                'court_position': player.court_position
            }
            serialized.append(player_data)

        return serialized

    def _serialize_team_classification(self, team_classification: Optional[TeamClassification]) -> Optional[Dict[str, Any]]:
        """Serialize team classification to dictionary."""
        if team_classification is None:
            return None

        return {
            'team_a_players': team_classification.team_a_players,
            'team_b_players': team_classification.team_b_players,
            'team_a_colors': {
                'primary_color': team_classification.team_a_colors.primary_color,
                'secondary_color': team_classification.team_a_colors.secondary_color,
                'color_name': team_classification.team_a_colors.color_name,
                'confidence': team_classification.team_a_colors.confidence
            },
            'team_b_colors': {
                'primary_color': team_classification.team_b_colors.primary_color,
                'secondary_color': team_classification.team_b_colors.secondary_color,
                'color_name': team_classification.team_b_colors.color_name,
                'confidence': team_classification.team_b_colors.confidence
            },
            'classification_confidence': team_classification.classification_confidence,
            'unclassified_players': team_classification.unclassified_players
        }

    def _serialize_ball_detection(self, ball_detection: Optional[BallDetection]) -> Optional[Dict[str, Any]]:
        """Serialize ball detection to dictionary."""
        if ball_detection is None:
            return None

        return {
            'detected': ball_detection.detected,
            'position': ball_detection.position,
            'court_position': ball_detection.court_position,
            'confidence': ball_detection.confidence,
            'velocity': ball_detection.velocity,
            'height_estimate': ball_detection.height_estimate,
            'possessing_player': ball_detection.possessing_player,
            'possessing_team': ball_detection.possessing_team
        }

    def reset_processing_state(self):
        """Reset processing state for new video."""
        self.current_homography = None
        self.frame_analyses.clear()
        self.processing_stats = {
            'total_frames': 0,
            'processed_frames': 0,
            'average_processing_time': 0.0,
            'total_processing_time': 0.0
        }

        # Reset detector states
        if self.player_detector:
            self.player_detector.reset_trackers()
        if self.team_classifier:
            self.team_classifier.clear_cache()
        if self.ball_detector:
            self.ball_detector.reset_tracking()

        logger.info("Video processor state reset")

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get summary statistics from all processed frames.

        Returns:
            Dictionary with summary statistics
        """
        if not self.frame_analyses:
            return {}

        try:
            # Player statistics
            all_players = set()
            team_a_players = set()
            team_b_players = set()

            # Ball statistics
            ball_detected_frames = 0
            total_ball_detections = 0

            # Court statistics
            court_detected_frames = 0

            for analysis in self.frame_analyses:
                # Count players
                if analysis.player_detections:
                    for player in analysis.player_detections:
                        all_players.add(player.player_id)
                        if player.team_id == 'team_a':
                            team_a_players.add(player.player_id)
                        elif player.team_id == 'team_b':
                            team_b_players.add(player.player_id)

                # Count ball detections
                if analysis.ball_detection and analysis.ball_detection.detected:
                    ball_detected_frames += 1
                    total_ball_detections += 1

                # Count court detections
                if (analysis.court_features and
                    analysis.court_features.confidence_score >= self.config.court_detection_confidence):
                    court_detected_frames += 1

            total_frames = len(self.frame_analyses)

            summary = {
                'total_frames_analyzed': total_frames,
                'total_unique_players': len(all_players),
                'team_a_players': len(team_a_players),
                'team_b_players': len(team_b_players),
                'ball_detection_rate': ball_detected_frames / total_frames if total_frames > 0 else 0,
                'court_detection_rate': court_detected_frames / total_frames if total_frames > 0 else 0,
                'average_players_per_frame': sum(len(a.player_detections) for a in self.frame_analyses) / total_frames if total_frames > 0 else 0,
                'processing_stats': self.processing_stats
            }

            return summary

        except Exception as e:
            logger.error(f"Error calculating summary statistics: {str(e)}")
            return {}

    async def process_video_stream(self, video_source: Any) -> AsyncGenerator[FrameAnalysis, None]:
        """
        Process a video stream (live or file) and yield frame analyses.

        Args:
            video_source: Video source (camera index, RTSP URL, etc.)

        Yields:
            FrameAnalysis objects for each processed frame
        """
        try:
            cap = cv2.VideoCapture(video_source)
            if not cap.isOpened():
                raise ValueError(f"Could not open video source: {video_source}")

            frame_number = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Process frame if it matches the sampling rate
                if frame_number % self.config.process_every_nth_frame == 0:
                    # For live streams, use current time as timestamp
                    timestamp = frame_number / 30.0  # Assume 30 FPS for live streams

                    analysis = await self._process_frame(frame, frame_number, timestamp)
                    yield analysis

                frame_number += 1

                # Yield control to allow other tasks
                await asyncio.sleep(0)

            cap.release()

        except Exception as e:
            logger.error(f"Error processing video stream: {str(e)}")
            raise
