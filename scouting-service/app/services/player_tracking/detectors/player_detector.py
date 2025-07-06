"""
Advanced basketball player detection and tracking service.

This module provides state-of-the-art player detection capabilities using:
- YOLOv11 for enhanced object detection
- ByteTrack/Basketball-SORT for robust multi-object tracking
- MediaPipe for pose estimation and player differentiation
- Enhanced OCR for jersey number recognition
- Temporal consistency and occlusion handling
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
import uuid
import math
from collections import defaultdict, deque

try:
    import supervision as sv
    SUPERVISION_AVAILABLE = True
except ImportError:
    SUPERVISION_AVAILABLE = False
    # Don't log warning during import to avoid container issues

logger = logging.getLogger(__name__)


@dataclass
class PlayerDetection:
    """Data class for storing player detection results."""
    player_id: str
    track_id: int  # Unique tracking ID
    bbox: Tuple[float, float, float, float]  # x1, y1, x2, y2
    confidence: float
    jersey_number: Optional[str] = None
    team_id: Optional[str] = None
    pose_keypoints: Optional[List[Tuple[float, float, float]]] = None  # x, y, confidence
    court_position: Optional[Tuple[float, float]] = None
    velocity: Optional[Tuple[float, float]] = None  # vx, vy
    tracking_confidence: float = 1.0  # Tracking stability
    occlusion_status: str = "visible"  # visible, partially_occluded, fully_occluded
    last_seen_frame: int = 0


class PlayerDetector:
    """
    Advanced basketball player detection using YOLO and enhanced tracking algorithms.

    This class implements a comprehensive player detection pipeline that includes:
    - Person detection using YOLOv11 models
    - ByteTrack/Basketball-SORT for robust multi-object tracking
    - Pose estimation for player differentiation
    - Enhanced jersey number recognition
    - Occlusion handling and temporal consistency
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced player detector.

        Args:
            config: Configuration dictionary with detection parameters
        """
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.4)  # Lower for better recall
        self.nms_threshold = self.config.get('nms_threshold', 0.4)
        self.tracking_method = self.config.get('tracking_method', 'bytetrack')  # bytetrack or basketball_sort

        # Basketball-specific parameters (define early for tracker initialization)
        self.basketball_params = {
            'max_occlusion_frames': 15,  # Frames to keep track during occlusion
            'min_track_length': 5,  # Minimum frames to establish a track
            'similarity_threshold': 0.7,  # For re-identification
            'pose_similarity_weight': 0.3,  # Weight for pose-based matching
            'appearance_similarity_weight': 0.4,  # Weight for appearance matching
            'motion_similarity_weight': 0.3,  # Weight for motion-based matching
        }

        # Update with user config
        if 'basketball_params' in self.config:
            self.basketball_params.update(self.config['basketball_params'])

        # Initialize YOLO model (YOLOv11)
        self.yolo_model = self._load_yolo_model()

        # Initialize tracking system
        self.tracker = self._initialize_tracker()

        # Initialize pose estimation
        self.pose_estimator = self._load_pose_estimator()

        # Initialize enhanced OCR for jersey numbers
        self.ocr_engine = self._load_ocr_engine()

        # Enhanced tracking state
        self.player_tracks = {}  # track_id -> PlayerTrack
        self.frame_count = 0
        self.court_homography = None

        logger.info(f"Enhanced PlayerDetector initialized with {self.tracking_method} tracking")
    
    def _load_yolo_model(self):
        """Load enhanced YOLO model for person detection."""
        try:
            from ultralytics import YOLO
            model_path = self.config.get('yolo_model_path', 'yolo11n.pt')
            model = YOLO(model_path)

            # Configure model for basketball detection
            model.overrides['conf'] = self.confidence_threshold
            model.overrides['iou'] = self.nms_threshold
            model.overrides['classes'] = [0]  # Person class only
            model.overrides['verbose'] = False

            logger.info(f"Loaded enhanced YOLO model: {model_path}")
            return model
        except ImportError:
            logger.warning("Ultralytics not available, using fallback detection")
            return None
        except Exception as e:
            logger.error(f"Error loading YOLO model: {str(e)}")
            return None

    def _initialize_tracker(self):
        """Initialize the tracking system."""
        if SUPERVISION_AVAILABLE and self.tracking_method == 'bytetrack':
            try:
                # Initialize ByteTracker with basketball-optimized parameters
                # Try different parameter names based on supervision version
                try:
                    tracker = sv.ByteTrack(
                        track_activation_threshold=0.4,  # Newer parameter name
                        lost_track_buffer=30,           # Newer parameter name
                        minimum_matching_threshold=0.8,  # Newer parameter name
                        frame_rate=30                    # Typical video frame rate
                    )
                except TypeError:
                    # Fallback to older parameter names
                    tracker = sv.ByteTrack(
                        track_thresh=0.4,  # Older parameter name
                        track_buffer=30,   # Older parameter name
                        match_thresh=0.8,  # Older parameter name
                        frame_rate=30      # Typical video frame rate
                    )
                logger.info("Initialized ByteTrack tracker")
                return tracker
            except Exception as e:
                logger.error(f"Error initializing ByteTrack: {str(e)}")

        # Fallback to custom Basketball-SORT implementation
        logger.info("Using custom Basketball-SORT tracker")
        return BasketballSORTTracker(self.basketball_params)

    def set_court_homography(self, homography: np.ndarray):
        """
        Set the court homography matrix for coordinate transformation.

        Args:
            homography: Homography matrix from court detection
        """
        self.court_homography = homography
        logger.debug("Court homography updated for player tracking")
    
    def _load_pose_estimator(self):
        """Load MediaPipe pose estimation model."""
        try:
            import mediapipe as mp
            mp_pose = mp.solutions.pose
            pose = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            logger.info("Loaded MediaPipe pose estimator")
            return pose
        except ImportError:
            logger.warning("MediaPipe not available, pose estimation disabled")
            return None
        except Exception as e:
            logger.error(f"Error loading pose estimator: {str(e)}")
            return None
    
    def _load_ocr_engine(self):
        """Load OCR engine for jersey number recognition."""
        try:
            import easyocr
            import os

            # Set cache directory to avoid permission issues
            os.environ.setdefault('EASYOCR_MODULE_PATH', '/tmp/easyocr')

            reader = easyocr.Reader(['en'], gpu=False)  # Use CPU for stability
            logger.info("Loaded EasyOCR engine")
            return reader
        except ImportError:
            logger.warning("EasyOCR not available, jersey number recognition disabled")
            return None
        except PermissionError as e:
            logger.warning(f"Permission error loading OCR engine: {str(e)}, jersey number recognition disabled")
            return None
        except Exception as e:
            logger.error(f"Error loading OCR engine: {str(e)}")
            return None
    
    def detect_players(self, frame: np.ndarray, frame_number: int = 0) -> List[PlayerDetection]:
        """
        Enhanced player detection and tracking in a video frame.

        Args:
            frame: Input video frame as numpy array (BGR format)
            frame_number: Current frame number for tracking

        Returns:
            List of PlayerDetection objects with enhanced tracking
        """
        try:
            logger.debug(f"Enhanced player detection in frame {frame_number}")
            self.frame_count = frame_number

            # Step 1: Detect persons using enhanced YOLO
            raw_detections = self._detect_persons_enhanced(frame)

            if not raw_detections:
                logger.debug("No persons detected")
                # Update tracker with empty detections to handle disappeared players
                if hasattr(self.tracker, 'update'):
                    try:
                        self.tracker.update([])
                    except:
                        pass
                return self._get_tracked_players_only()

            # Step 2: Update tracking system
            tracked_detections = self._update_enhanced_tracking(raw_detections, frame)

            # Step 3: Enhance detections with additional information
            enhanced_players = []
            for detection in tracked_detections:
                # Add pose estimation for player differentiation
                if self.pose_estimator:
                    detection.pose_keypoints = self._estimate_pose_enhanced(frame, detection.bbox)

                # Add jersey number recognition with improved accuracy
                if self.ocr_engine:
                    detection.jersey_number = self._recognize_jersey_number_enhanced(frame, detection.bbox)

                # Calculate court position if homography is available
                if self.court_homography is not None:
                    detection.court_position = self._calculate_court_position(detection.bbox)

                # Calculate velocity from tracking history
                detection.velocity = self._calculate_player_velocity(detection.track_id)

                # Assess occlusion status
                detection.occlusion_status = self._assess_occlusion_status(detection, frame)

                enhanced_players.append(detection)

            # Step 4: Apply Basketball-specific post-processing
            enhanced_players = self._apply_basketball_postprocessing(enhanced_players, frame)

            logger.debug(f"Enhanced detection: {len(enhanced_players)} players tracked in frame {frame_number}")
            return enhanced_players

        except Exception as e:
            logger.error(f"Error in enhanced player detection: {str(e)}")
            return []

    def _detect_persons_enhanced(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Enhanced person detection using YOLO with basketball-specific optimizations.

        Args:
            frame: Input video frame

        Returns:
            List of detection dictionaries with enhanced information
        """
        detections = []

        if self.yolo_model is not None:
            try:
                # Run YOLO inference with enhanced parameters
                results = self.yolo_model(frame, classes=[0], verbose=False)

                for result in results:
                    if hasattr(result, 'boxes') and result.boxes is not None:
                        for box in result.boxes:
                            # Extract detection data
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            confidence = float(box.conf[0])

                            # Apply basketball-specific filtering
                            if confidence >= self.confidence_threshold:
                                # Calculate additional features for tracking
                                bbox_area = (x2 - x1) * (y2 - y1)
                                aspect_ratio = (y2 - y1) / (x2 - x1) if (x2 - x1) > 0 else 0

                                # Filter based on reasonable player dimensions
                                if (bbox_area > 500 and  # Minimum size
                                    aspect_ratio > 1.2 and aspect_ratio < 4.0):  # Human-like aspect ratio

                                    detections.append({
                                        'bbox': (x1, y1, x2, y2),
                                        'confidence': confidence,
                                        'area': bbox_area,
                                        'aspect_ratio': aspect_ratio,
                                        'center': ((x1 + x2) / 2, (y1 + y2) / 2)
                                    })

            except Exception as e:
                logger.error(f"Error in enhanced YOLO detection: {str(e)}")
                # Fallback to basic detection
                detections = self._fallback_person_detection(frame)
        else:
            # Use fallback detection
            detections = self._fallback_person_detection(frame)

        return detections

    def _update_enhanced_tracking(self, detections: List[Dict[str, Any]],
                                frame: np.ndarray) -> List[PlayerDetection]:
        """
        Update tracking system with enhanced Basketball-SORT algorithm.

        Args:
            detections: List of detection dictionaries
            frame: Current frame

        Returns:
            List of tracked PlayerDetection objects
        """
        tracked_players = []

        if SUPERVISION_AVAILABLE and hasattr(self.tracker, 'update'):
            try:
                # Convert detections to supervision format
                detections_sv = []
                for det in detections:
                    x1, y1, x2, y2 = det['bbox']
                    detections_sv.append([x1, y1, x2, y2, det['confidence']])

                if detections_sv:
                    detections_array = np.array(detections_sv)
                    tracks = self.tracker.update(detections_array)

                    # Convert tracks back to PlayerDetection objects
                    for track in tracks:
                        x1, y1, x2, y2, track_id = track[:5]
                        confidence = track[4] if len(track) > 4 else 0.8

                        player = PlayerDetection(
                            player_id=f"player_{track_id}",
                            track_id=int(track_id),
                            bbox=(float(x1), float(y1), float(x2), float(y2)),
                            confidence=float(confidence),
                            last_seen_frame=self.frame_count
                        )
                        tracked_players.append(player)

            except Exception as e:
                logger.error(f"Error in ByteTrack update: {str(e)}")
                # Fallback to custom tracking
                tracked_players = self._custom_basketball_tracking(detections, frame)
        else:
            # Use custom Basketball-SORT implementation
            tracked_players = self._custom_basketball_tracking(detections, frame)

        return tracked_players

    def _custom_basketball_tracking(self, detections: List[Dict[str, Any]],
                                   frame: np.ndarray) -> List[PlayerDetection]:
        """
        Custom Basketball-SORT tracking implementation.

        Args:
            detections: List of detection dictionaries
            frame: Current frame

        Returns:
            List of tracked PlayerDetection objects
        """
        tracked_players = []

        # Convert detections to tracking format
        current_detections = []
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            current_detections.append({
                'bbox': (x1, y1, x2, y2),
                'confidence': det['confidence'],
                'center': det['center'],
                'area': det['area'],
                'features': self._extract_appearance_features(frame, (x1, y1, x2, y2))
            })

        # Update existing tracks
        updated_tracks = {}
        unmatched_detections = list(range(len(current_detections)))

        # Match detections to existing tracks
        if self.player_tracks:
            matches, unmatched_tracks, unmatched_detections = self._associate_detections_to_tracks(
                current_detections, self.player_tracks
            )

            # Update matched tracks
            for det_idx, track_id in matches:
                detection = current_detections[det_idx]
                track = self.player_tracks[track_id]

                # Update track with new detection
                track.update(detection, self.frame_count)
                updated_tracks[track_id] = track

                # Create PlayerDetection object
                player = PlayerDetection(
                    player_id=f"player_{track_id}",
                    track_id=track_id,
                    bbox=detection['bbox'],
                    confidence=detection['confidence'],
                    tracking_confidence=track.confidence,
                    last_seen_frame=self.frame_count
                )
                tracked_players.append(player)

            # Handle unmatched tracks (potential occlusions)
            for track_id in unmatched_tracks:
                track = self.player_tracks[track_id]
                if self.frame_count - track.last_seen_frame < self.basketball_params['max_occlusion_frames']:
                    # Keep track during occlusion
                    track.predict(self.frame_count)
                    updated_tracks[track_id] = track

                    # Create PlayerDetection with predicted position
                    player = PlayerDetection(
                        player_id=f"player_{track_id}",
                        track_id=track_id,
                        bbox=track.predicted_bbox,
                        confidence=0.3,  # Lower confidence for predicted
                        tracking_confidence=track.confidence * 0.8,
                        occlusion_status="partially_occluded",
                        last_seen_frame=track.last_seen_frame
                    )
                    tracked_players.append(player)

        # Create new tracks for unmatched detections
        for det_idx in unmatched_detections:
            detection = current_detections[det_idx]
            track_id = self._get_next_track_id()

            new_track = PlayerTrack(
                track_id=track_id,
                initial_detection=detection,
                frame_number=self.frame_count,
                params=self.basketball_params
            )
            updated_tracks[track_id] = new_track

            # Create PlayerDetection object
            player = PlayerDetection(
                player_id=f"player_{track_id}",
                track_id=track_id,
                bbox=detection['bbox'],
                confidence=detection['confidence'],
                tracking_confidence=1.0,
                last_seen_frame=self.frame_count
            )
            tracked_players.append(player)

        # Update track storage
        self.player_tracks = updated_tracks

        return tracked_players

    def _get_next_track_id(self) -> int:
        """Get next available track ID."""
        if not hasattr(self, '_next_track_id'):
            self._next_track_id = 1
        track_id = self._next_track_id
        self._next_track_id += 1
        return track_id

    def _get_tracked_players_only(self) -> List[PlayerDetection]:
        """Get currently tracked players without new detections."""
        tracked_players = []

        for track_id, track in self.player_tracks.items():
            if self.frame_count - track.last_seen_frame < self.basketball_params['max_occlusion_frames']:
                # Predict position for occluded players
                track.predict(self.frame_count)

                player = PlayerDetection(
                    player_id=f"player_{track_id}",
                    track_id=track_id,
                    bbox=track.predicted_bbox,
                    confidence=0.2,  # Lower confidence for predicted
                    tracking_confidence=track.confidence * 0.6,
                    occlusion_status="occluded",
                    last_seen_frame=track.last_seen_frame
                )
                tracked_players.append(player)

        return tracked_players

    def _associate_detections_to_tracks(self, detections: List[Dict[str, Any]],
                                      tracks: Dict[int, Any]) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
        """
        Associate detections to existing tracks.

        Args:
            detections: List of current detections
            tracks: Dictionary of existing tracks

        Returns:
            Tuple of (matches, unmatched_tracks, unmatched_detections)
        """
        if not tracks or not detections:
            return [], list(tracks.keys()), list(range(len(detections)))

        # Simple distance-based matching for now
        matches = []
        unmatched_detections = list(range(len(detections)))
        unmatched_tracks = list(tracks.keys())

        # Calculate distances between detections and tracks
        for det_idx, detection in enumerate(detections):
            det_center = detection['center']
            best_track = None
            best_distance = float('inf')

            for track_id, track in tracks.items():
                if hasattr(track, 'bbox_history') and track.bbox_history:
                    track_bbox = track.bbox_history[-1]
                    track_center = ((track_bbox[0] + track_bbox[2]) / 2, (track_bbox[1] + track_bbox[3]) / 2)

                    distance = math.sqrt(
                        (det_center[0] - track_center[0])**2 +
                        (det_center[1] - track_center[1])**2
                    )

                    if distance < best_distance and distance < 100:  # Distance threshold
                        best_distance = distance
                        best_track = track_id

            if best_track is not None:
                matches.append((det_idx, best_track))
                if det_idx in unmatched_detections:
                    unmatched_detections.remove(det_idx)
                if best_track in unmatched_tracks:
                    unmatched_tracks.remove(best_track)

        return matches, unmatched_tracks, unmatched_detections

    def _extract_appearance_features(self, frame: np.ndarray, bbox: Tuple[float, float, float, float]) -> List[float]:
        """
        Extract appearance features from player bounding box.

        Args:
            frame: Input frame
            bbox: Player bounding box

        Returns:
            List of appearance features
        """
        try:
            x1, y1, x2, y2 = [int(coord) for coord in bbox]

            # Ensure coordinates are within frame bounds
            h, w = frame.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 <= x1 or y2 <= y1:
                return []

            # Extract player region
            player_region = frame[y1:y2, x1:x2]

            # Simple color histogram as features
            hist_b = cv2.calcHist([player_region], [0], None, [32], [0, 256])
            hist_g = cv2.calcHist([player_region], [1], None, [32], [0, 256])
            hist_r = cv2.calcHist([player_region], [2], None, [32], [0, 256])

            # Normalize and flatten
            features = []
            for hist in [hist_b, hist_g, hist_r]:
                hist = cv2.normalize(hist, hist).flatten()
                features.extend(hist.tolist())

            return features

        except Exception as e:
            logger.error(f"Error extracting appearance features: {str(e)}")
            return []

    def _estimate_pose_enhanced(self, frame: np.ndarray, bbox: Tuple[float, float, float, float]) -> Optional[List[Tuple[float, float, float]]]:
        """
        Enhanced pose estimation for player differentiation.

        Args:
            frame: Input frame
            bbox: Player bounding box

        Returns:
            List of pose keypoints or None if estimation fails
        """
        if self.pose_estimator is None:
            return None

        try:
            x1, y1, x2, y2 = [int(coord) for coord in bbox]

            # Ensure coordinates are within frame bounds
            h, w = frame.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 <= x1 or y2 <= y1:
                return None

            # Extract player region
            player_region = frame[y1:y2, x1:x2]
            player_rgb = cv2.cvtColor(player_region, cv2.COLOR_BGR2RGB)

            # Run pose estimation
            results = self.pose_estimator.process(player_rgb)

            if results.pose_landmarks:
                keypoints = []
                for landmark in results.pose_landmarks.landmark:
                    # Convert relative coordinates to absolute
                    x = landmark.x * (x2 - x1) + x1
                    y = landmark.y * (y2 - y1) + y1
                    confidence = landmark.visibility
                    keypoints.append((x, y, confidence))
                return keypoints

            return None

        except Exception as e:
            logger.error(f"Error in enhanced pose estimation: {str(e)}")
            return None

    def _recognize_jersey_number_enhanced(self, frame: np.ndarray, bbox: Tuple[float, float, float, float]) -> Optional[str]:
        """
        Enhanced jersey number recognition with improved accuracy.

        Args:
            frame: Input frame
            bbox: Player bounding box

        Returns:
            Recognized jersey number or None if recognition fails
        """
        if self.ocr_engine is None:
            return None

        try:
            x1, y1, x2, y2 = [int(coord) for coord in bbox]

            # Ensure coordinates are within frame bounds
            h, w = frame.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 <= x1 or y2 <= y1:
                return None

            # Extract player region
            player_region = frame[y1:y2, x1:x2]

            # Focus on upper torso area where jersey numbers are typically located
            torso_height = int((y2 - y1) * 0.6)
            torso_region = player_region[:torso_height, :]

            # Enhance image for better OCR
            gray = cv2.cvtColor(torso_region, cv2.COLOR_BGR2GRAY)

            # Apply contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Run OCR
            results = self.ocr_engine.readtext(enhanced)

            # Filter results for jersey numbers (typically 1-2 digits)
            for (bbox_ocr, text, confidence) in results:
                if confidence > 0.5 and text.isdigit() and 1 <= len(text) <= 2:
                    return text

            return None

        except Exception as e:
            logger.error(f"Error in enhanced jersey number recognition: {str(e)}")
            return None

    def _calculate_court_position(self, bbox: Tuple[float, float, float, float]) -> Optional[Tuple[float, float]]:
        """
        Calculate player position on court using homography.

        Args:
            bbox: Player bounding box

        Returns:
            Court position or None if homography not available
        """
        if self.court_homography is None:
            return None

        try:
            # Use bottom center of bounding box as player position
            x1, y1, x2, y2 = bbox
            player_point = np.array([[(x1 + x2) / 2, y2]], dtype=np.float32)

            # Transform to court coordinates
            court_point = cv2.perspectiveTransform(player_point.reshape(1, 1, 2), self.court_homography)

            return (float(court_point[0][0][0]), float(court_point[0][0][1]))

        except Exception as e:
            logger.error(f"Error calculating court position: {str(e)}")
            return None

    def _calculate_player_velocity(self, track_id: int) -> Optional[Tuple[float, float]]:
        """
        Calculate player velocity from tracking history.

        Args:
            track_id: Player track ID

        Returns:
            Velocity (vx, vy) or None if insufficient history
        """
        if track_id not in self.player_tracks:
            return None

        track = self.player_tracks[track_id]

        if hasattr(track, 'velocity'):
            return track.velocity

        return None

    def _assess_occlusion_status(self, detection: PlayerDetection, frame: np.ndarray) -> str:
        """
        Assess player occlusion status.

        Args:
            detection: Player detection
            frame: Current frame

        Returns:
            Occlusion status string
        """
        # Simple heuristic based on detection confidence
        if detection.confidence > 0.7:
            return "visible"
        elif detection.confidence > 0.3:
            return "partially_occluded"
        else:
            return "fully_occluded"

    def _apply_basketball_postprocessing(self, players: List[PlayerDetection], frame: np.ndarray) -> List[PlayerDetection]:
        """
        Apply basketball-specific post-processing to player detections.

        Args:
            players: List of player detections
            frame: Current frame

        Returns:
            Post-processed player detections
        """
        # For now, just return the players as-is
        # This could include team classification, formation analysis, etc.
        return players
    
    def _detect_persons(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect persons in the frame using YOLO.
        
        Args:
            frame: Input frame
            
        Returns:
            List of detection dictionaries
        """
        detections = []
        
        if self.yolo_model is not None:
            try:
                # Run YOLO inference
                results = self.yolo_model(frame, classes=[0], verbose=False)  # Class 0 is person
                
                for result in results:
                    if hasattr(result, 'boxes') and result.boxes is not None:
                        for box in result.boxes:
                            # Extract detection data
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            confidence = float(box.conf[0])
                            
                            if confidence >= self.confidence_threshold:
                                detections.append({
                                    'bbox': (x1, y1, x2, y2),
                                    'confidence': confidence
                                })
                
            except Exception as e:
                logger.error(f"Error in YOLO detection: {str(e)}")
                # Fallback to OpenCV HOG detector
                detections = self._fallback_person_detection(frame)
        else:
            # Use fallback detection
            detections = self._fallback_person_detection(frame)
        
        return detections
    
    def _fallback_person_detection(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Fallback person detection using OpenCV HOG detector.

        Args:
            frame: Input frame

        Returns:
            List of detection dictionaries
        """
        try:
            # Initialize HOG detector
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

            # Detect people
            boxes, weights = hog.detectMultiScale(
                frame,
                winStride=(8, 8),
                padding=(4, 4),
                scale=1.05
            )

            detections = []
            for i, (x, y, w, h) in enumerate(boxes):
                confidence = float(weights[i])
                if confidence >= self.confidence_threshold:
                    x1, y1, x2, y2 = x, y, x + w, y + h
                    bbox_area = w * h
                    aspect_ratio = h / w if w > 0 else 0

                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'confidence': confidence,
                        'area': bbox_area,
                        'aspect_ratio': aspect_ratio,
                        'center': ((x1 + x2) / 2, (y1 + y2) / 2)
                    })

            return detections

        except Exception as e:
            logger.error(f"Error in fallback detection: {str(e)}")
            return []
    
    def _update_trackers(self, detections: List[Dict[str, Any]], 
                        frame: np.ndarray, frame_number: int) -> List[PlayerDetection]:
        """
        Update player trackers with new detections.
        
        Args:
            detections: List of new detections
            frame: Current frame
            frame_number: Current frame number
            
        Returns:
            List of tracked players
        """
        # Simple tracking implementation
        # In a production system, you would use more sophisticated tracking like DeepSORT
        
        tracked_players = []
        
        # Match detections to existing trackers
        for detection in detections:
            bbox = detection['bbox']
            confidence = detection['confidence']
            
            # Find best matching tracker
            best_match = None
            best_distance = float('inf')
            
            for player_id, tracker in self.trackers.items():
                if tracker['active']:
                    # Calculate distance between detection and tracker
                    distance = self._calculate_bbox_distance(bbox, tracker['bbox'])
                    if distance < best_distance and distance < 100:  # Threshold for matching
                        best_distance = distance
                        best_match = player_id
            
            if best_match:
                # Update existing tracker
                self.trackers[best_match]['bbox'] = bbox
                self.trackers[best_match]['confidence'] = confidence
                self.trackers[best_match]['last_seen'] = frame_number
                player_id = best_match
            else:
                # Create new tracker
                player_id = f"player_{self.next_player_id}"
                self.next_player_id += 1
                self.trackers[player_id] = {
                    'bbox': bbox,
                    'confidence': confidence,
                    'last_seen': frame_number,
                    'active': True
                }
            
            tracked_players.append(PlayerDetection(
                player_id=player_id,
                bbox=bbox,
                confidence=confidence
            ))
        
        # Mark inactive trackers
        for player_id, tracker in self.trackers.items():
            if frame_number - tracker['last_seen'] > self.max_disappeared:
                tracker['active'] = False
        
        return tracked_players
    
    def _calculate_bbox_distance(self, bbox1: Tuple[float, float, float, float],
                                bbox2: Tuple[float, float, float, float]) -> float:
        """
        Calculate distance between two bounding boxes.
        
        Args:
            bbox1: First bounding box (x1, y1, x2, y2)
            bbox2: Second bounding box (x1, y1, x2, y2)
            
        Returns:
            Distance between bounding box centers
        """
        # Calculate centers
        center1 = ((bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2)
        center2 = ((bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2)
        
        # Calculate Euclidean distance
        distance = np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
        return distance

    def _estimate_pose(self, frame: np.ndarray,
                      bbox: Tuple[float, float, float, float]) -> Optional[List[Tuple[float, float, float]]]:
        """
        Estimate pose keypoints for a player.

        Args:
            frame: Input frame
            bbox: Player bounding box (x1, y1, x2, y2)

        Returns:
            List of pose keypoints (x, y, confidence) or None if estimation fails
        """
        if self.pose_estimator is None:
            return None

        try:
            # Extract player region
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            x1, y1 = max(0, x1), max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)

            if x2 <= x1 or y2 <= y1:
                return None

            player_region = frame[y1:y2, x1:x2]

            # Convert BGR to RGB for MediaPipe
            rgb_region = cv2.cvtColor(player_region, cv2.COLOR_BGR2RGB)

            # Process with MediaPipe
            results = self.pose_estimator.process(rgb_region)

            if results.pose_landmarks:
                keypoints = []
                for landmark in results.pose_landmarks.landmark:
                    # Convert relative coordinates to absolute coordinates
                    x = x1 + landmark.x * (x2 - x1)
                    y = y1 + landmark.y * (y2 - y1)
                    confidence = landmark.visibility
                    keypoints.append((float(x), float(y), float(confidence)))

                return keypoints

            return None

        except Exception as e:
            logger.error(f"Error in pose estimation: {str(e)}")
            return None

    def _recognize_jersey_number(self, frame: np.ndarray,
                                bbox: Tuple[float, float, float, float]) -> Optional[str]:
        """
        Recognize jersey number from player bounding box.

        Args:
            frame: Input frame
            bbox: Player bounding box (x1, y1, x2, y2)

        Returns:
            Recognized jersey number as string or None if recognition fails
        """
        if self.ocr_engine is None:
            return None

        try:
            # Extract player region
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            x1, y1 = max(0, x1), max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)

            if x2 <= x1 or y2 <= y1:
                return None

            player_region = frame[y1:y2, x1:x2]

            # Focus on upper torso area where jersey numbers are typically located
            height = y2 - y1
            jersey_y1 = int(height * 0.1)  # Start from 10% down
            jersey_y2 = int(height * 0.6)  # End at 60% down

            if jersey_y2 <= jersey_y1:
                return None

            jersey_region = player_region[jersey_y1:jersey_y2, :]

            # Preprocess for better OCR
            gray = cv2.cvtColor(jersey_region, cv2.COLOR_BGR2GRAY)

            # Apply contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Apply threshold to get binary image
            _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Run OCR
            results = self.ocr_engine.readtext(binary)

            # Filter results for numbers
            for (bbox_ocr, text, confidence) in results:
                if confidence > 0.5:  # Confidence threshold
                    # Check if text contains digits
                    digits = ''.join(filter(str.isdigit, text))
                    if digits and len(digits) <= 3:  # Valid jersey numbers are 1-3 digits
                        return digits

            return None

        except Exception as e:
            logger.error(f"Error in jersey number recognition: {str(e)}")
            return None

    def get_active_players(self) -> List[str]:
        """
        Get list of currently active player IDs.

        Returns:
            List of active player IDs
        """
        return [player_id for player_id, tracker in self.trackers.items()
                if tracker['active']]

    def reset_trackers(self):
        """Reset all player trackers."""
        self.trackers.clear()
        self.next_player_id = 1
        logger.info("Player trackers reset")

    def set_court_homography(self, homography_matrix: np.ndarray):
        """
        Set the court homography matrix for coordinate transformation.

        Args:
            homography_matrix: 3x3 homography transformation matrix
        """
        self.homography_matrix = homography_matrix
        logger.info("Court homography matrix set for player detector")

    def transform_to_court_coordinates(self, bbox: Tuple[float, float, float, float]) -> Optional[Tuple[float, float]]:
        """
        Transform player position to court coordinates.

        Args:
            bbox: Player bounding box (x1, y1, x2, y2)

        Returns:
            Player position in court coordinates (x, y) or None if transformation fails
        """
        if not hasattr(self, 'homography_matrix') or self.homography_matrix is None:
            return None

        try:
            # Use bottom center of bounding box as player position
            x1, y1, x2, y2 = bbox
            player_x = (x1 + x2) / 2
            player_y = y2  # Bottom of bounding box

            # Transform to court coordinates
            point_homogeneous = np.array([[player_x, player_y, 1.0]], dtype=np.float32).T
            transformed = self.homography_matrix @ point_homogeneous

            if transformed[2, 0] != 0:
                court_x = transformed[0, 0] / transformed[2, 0]
                court_y = transformed[1, 0] / transformed[2, 0]
                return (float(court_x), float(court_y))

            return None

        except Exception as e:
            logger.error(f"Error transforming to court coordinates: {str(e)}")
            return None


class PlayerTrack:
    """
    Enhanced player track for Basketball-SORT algorithm.

    This class maintains the state of a tracked player across frames,
    handling occlusions, appearance changes, and motion prediction.
    """

    def __init__(self, track_id: int, initial_detection: Dict[str, Any],
                 frame_number: int, params: Dict[str, Any]):
        """
        Initialize a new player track.

        Args:
            track_id: Unique track identifier
            initial_detection: Initial detection dictionary
            frame_number: Frame number when track was created
            params: Basketball-specific parameters
        """
        self.track_id = track_id
        self.bbox_history = deque(maxlen=10)
        self.confidence_history = deque(maxlen=5)
        self.appearance_features = deque(maxlen=3)

        # Initialize with first detection
        self.bbox_history.append(initial_detection['bbox'])
        self.confidence_history.append(initial_detection['confidence'])
        self.appearance_features.append(initial_detection.get('features', []))

        self.last_seen_frame = frame_number
        self.created_frame = frame_number
        self.confidence = 1.0
        self.predicted_bbox = initial_detection['bbox']

        # Motion model (simple linear prediction)
        self.velocity = (0.0, 0.0)
        self.params = params

    def update(self, detection: Dict[str, Any], frame_number: int):
        """
        Update track with new detection.

        Args:
            detection: New detection dictionary
            frame_number: Current frame number
        """
        # Update history
        self.bbox_history.append(detection['bbox'])
        self.confidence_history.append(detection['confidence'])
        if 'features' in detection:
            self.appearance_features.append(detection['features'])

        # Update velocity
        if len(self.bbox_history) >= 2:
            prev_center = self._get_bbox_center(self.bbox_history[-2])
            curr_center = self._get_bbox_center(self.bbox_history[-1])
            self.velocity = (
                curr_center[0] - prev_center[0],
                curr_center[1] - prev_center[1]
            )

        self.last_seen_frame = frame_number
        self.confidence = min(1.0, self.confidence + 0.1)  # Increase confidence
        self.predicted_bbox = detection['bbox']

    def predict(self, frame_number: int):
        """
        Predict track position for current frame.

        Args:
            frame_number: Current frame number
        """
        if not self.bbox_history:
            return

        # Simple linear motion prediction
        last_bbox = self.bbox_history[-1]
        frames_since_update = frame_number - self.last_seen_frame

        # Predict new center
        last_center = self._get_bbox_center(last_bbox)
        predicted_center = (
            last_center[0] + self.velocity[0] * frames_since_update,
            last_center[1] + self.velocity[1] * frames_since_update
        )

        # Maintain bbox size
        bbox_width = last_bbox[2] - last_bbox[0]
        bbox_height = last_bbox[3] - last_bbox[1]

        self.predicted_bbox = (
            predicted_center[0] - bbox_width / 2,
            predicted_center[1] - bbox_height / 2,
            predicted_center[0] + bbox_width / 2,
            predicted_center[1] + bbox_height / 2
        )

        # Decrease confidence over time
        self.confidence *= 0.9

    def _get_bbox_center(self, bbox: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """Get center point of bounding box."""
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

    def get_age(self, current_frame: int) -> int:
        """Get age of track in frames."""
        return current_frame - self.created_frame

    def is_stable(self) -> bool:
        """Check if track is stable enough for output."""
        return self.get_age(self.last_seen_frame) >= self.params.get('min_track_length', 5)


class BasketballSORTTracker:
    """
    Basketball-SORT tracker implementation for enhanced player tracking.

    This tracker is specifically designed for basketball scenarios with:
    - Enhanced occlusion handling
    - Pose-based similarity matching
    - Basketball-specific motion models
    """

    def __init__(self, params: Dict[str, Any]):
        """
        Initialize Basketball-SORT tracker.

        Args:
            params: Basketball-specific parameters
        """
        self.params = params
        self.tracks = {}
        self.next_track_id = 1
        self.frame_count = 0

    def update(self, detections: List[Dict[str, Any]]) -> List[PlayerDetection]:
        """
        Update tracker with new detections.

        Args:
            detections: List of detection dictionaries

        Returns:
            List of tracked PlayerDetection objects
        """
        self.frame_count += 1

        # Implementation would go here - this is a placeholder
        # for the full Basketball-SORT algorithm

        return []
