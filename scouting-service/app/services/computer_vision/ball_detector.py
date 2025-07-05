"""
Basketball detection and tracking service.

This module provides advanced basketball detection capabilities using:
- YOLO models for object detection
- Color-based detection as fallback
- Kalman filtering for smooth tracking
- Possession analysis
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BallDetection:
    """Data class for storing ball detection results."""
    detected: bool
    position: Optional[Tuple[float, float]] = None  # x, y in image coordinates
    court_position: Optional[Tuple[float, float]] = None  # x, y in court coordinates
    confidence: float = 0.0
    velocity: Optional[Tuple[float, float]] = None  # vx, vy
    height_estimate: Optional[float] = None  # Estimated height above court
    possessing_player: Optional[str] = None
    possessing_team: Optional[str] = None


class BallDetector:
    """
    Advanced basketball detection using multiple computer vision techniques.
    
    This class implements a robust ball detection pipeline that can handle:
    - Various lighting conditions
    - Ball occlusion by players
    - Fast ball movement
    - Different camera angles
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ball detector.
        
        Args:
            config: Configuration dictionary with detection parameters
        """
        self.config = config or {}
        self.confidence_threshold = self.config.get('confidence_threshold', 0.3)
        
        # Initialize YOLO model for ball detection
        self.yolo_model = self._load_yolo_model()
        
        # Ball tracking state
        self.previous_positions = []
        self.max_position_history = 10
        self.kalman_filter = self._initialize_kalman_filter()
        
        # Ball characteristics for color-based detection
        self.ball_color_ranges = {
            'orange': {
                'lower': np.array([5, 100, 150]),
                'upper': np.array([25, 255, 255])
            },
            'brown': {
                'lower': np.array([8, 50, 100]),
                'upper': np.array([20, 255, 200])
            }
        }
        
        # Court homography matrix for coordinate transformation
        self.homography_matrix = None
        
        logger.info("BallDetector initialized successfully")
    
    def _load_yolo_model(self):
        """Load YOLO model for ball detection."""
        try:
            from ultralytics import YOLO
            model_path = self.config.get('yolo_model_path', 'yolo11n.pt')
            model = YOLO(model_path)
            logger.info(f"Loaded YOLO model for ball detection: {model_path}")
            return model
        except ImportError:
            logger.warning("Ultralytics not available, using fallback ball detection")
            return None
        except Exception as e:
            logger.error(f"Error loading YOLO model: {str(e)}")
            return None
    
    def _initialize_kalman_filter(self):
        """Initialize Kalman filter for ball tracking."""
        try:
            # Create Kalman filter for 2D position and velocity tracking
            kalman = cv2.KalmanFilter(4, 2)  # 4 state variables, 2 measurements
            
            # State transition matrix (position and velocity)
            kalman.transitionMatrix = np.array([
                [1, 0, 1, 0],  # x = x + vx
                [0, 1, 0, 1],  # y = y + vy
                [0, 0, 1, 0],  # vx = vx
                [0, 0, 0, 1]   # vy = vy
            ], dtype=np.float32)
            
            # Measurement matrix (we measure position only)
            kalman.measurementMatrix = np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0]
            ], dtype=np.float32)
            
            # Process noise covariance
            kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 0.1
            
            # Measurement noise covariance
            kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 10
            
            # Error covariance
            kalman.errorCovPost = np.eye(4, dtype=np.float32)
            
            return kalman
            
        except Exception as e:
            logger.error(f"Error initializing Kalman filter: {str(e)}")
            return None
    
    def detect_ball(self, frame: np.ndarray, frame_number: int = 0) -> BallDetection:
        """
        Detect basketball in a video frame.
        
        Args:
            frame: Input video frame as numpy array (BGR format)
            frame_number: Current frame number for tracking
            
        Returns:
            BallDetection object with detection results
        """
        try:
            logger.debug(f"Detecting ball in frame {frame_number}")
            
            # Try YOLO detection first
            ball_position = None
            confidence = 0.0
            
            if self.yolo_model is not None:
                ball_position, confidence = self._detect_ball_yolo(frame)
            
            # Fallback to color-based detection if YOLO fails
            if ball_position is None or confidence < self.confidence_threshold:
                ball_position, fallback_confidence = self._detect_ball_color(frame)
                if ball_position is not None:
                    confidence = max(confidence, fallback_confidence)
            
            # Create detection result
            if ball_position is not None:
                # Update tracking
                predicted_position = self._update_tracking(ball_position)
                
                # Calculate velocity
                velocity = self._calculate_velocity()
                
                # Estimate height
                height_estimate = self._estimate_ball_height(frame, ball_position)
                
                # Transform to court coordinates
                court_position = self._transform_to_court_coordinates(ball_position)
                
                detection = BallDetection(
                    detected=True,
                    position=ball_position,
                    court_position=court_position,
                    confidence=confidence,
                    velocity=velocity,
                    height_estimate=height_estimate
                )
                
                logger.debug(f"Ball detected at position {ball_position} with confidence {confidence}")
                return detection
            else:
                logger.debug("No ball detected")
                return BallDetection(detected=False)
                
        except Exception as e:
            logger.error(f"Error in ball detection: {str(e)}")
            return BallDetection(detected=False)
    
    def _detect_ball_yolo(self, frame: np.ndarray) -> Tuple[Optional[Tuple[float, float]], float]:
        """
        Detect ball using YOLO model.
        
        Args:
            frame: Input frame
            
        Returns:
            Tuple of (ball_position, confidence) or (None, 0.0)
        """
        try:
            # Run YOLO inference
            results = self.yolo_model(frame, classes=[32], verbose=False)  # Class 32 is sports ball
            
            best_detection = None
            best_confidence = 0.0
            
            for result in results:
                if hasattr(result, 'boxes') and result.boxes is not None:
                    for box in result.boxes:
                        confidence = float(box.conf[0])
                        
                        if confidence > best_confidence and confidence >= self.confidence_threshold:
                            # Get bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            
                            # Calculate center of the ball
                            center_x = (x1 + x2) / 2
                            center_y = (y1 + y2) / 2
                            
                            best_detection = (center_x, center_y)
                            best_confidence = confidence
            
            return best_detection, best_confidence
            
        except Exception as e:
            logger.error(f"Error in YOLO ball detection: {str(e)}")
            return None, 0.0
    
    def _detect_ball_color(self, frame: np.ndarray) -> Tuple[Optional[Tuple[float, float]], float]:
        """
        Detect ball using color-based detection.
        
        Args:
            frame: Input frame
            
        Returns:
            Tuple of (ball_position, confidence) or (None, 0.0)
        """
        try:
            # Convert to HSV color space
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            best_detection = None
            best_confidence = 0.0
            
            # Try different color ranges
            for color_name, color_range in self.ball_color_ranges.items():
                # Create mask for the color
                mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
                
                # Apply morphological operations to clean up the mask
                kernel = np.ones((5, 5), np.uint8)
                mask = cv2.erode(mask, kernel, iterations=1)
                mask = cv2.dilate(mask, kernel, iterations=2)
                
                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    # Filter by area
                    area = cv2.contourArea(contour)
                    if area < 50 or area > 5000:  # Reasonable ball size range
                        continue
                    
                    # Check circularity
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter == 0:
                        continue
                    
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    
                    if circularity > 0.5:  # Reasonably circular
                        # Calculate center
                        M = cv2.moments(contour)
                        if M["m00"] != 0:
                            center_x = M["m10"] / M["m00"]
                            center_y = M["m01"] / M["m00"]
                            
                            # Calculate confidence based on circularity and size
                            confidence = circularity * min(1.0, area / 1000.0)
                            
                            if confidence > best_confidence:
                                best_detection = (center_x, center_y)
                                best_confidence = confidence
            
            return best_detection, best_confidence
            
        except Exception as e:
            logger.error(f"Error in color-based ball detection: {str(e)}")
            return None, 0.0
    
    def _update_tracking(self, ball_position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Update ball tracking with Kalman filter.
        
        Args:
            ball_position: Detected ball position
            
        Returns:
            Predicted/smoothed ball position
        """
        try:
            if self.kalman_filter is None:
                return ball_position
            
            # Update Kalman filter with measurement
            measurement = np.array([[ball_position[0]], [ball_position[1]]], dtype=np.float32)
            
            if len(self.previous_positions) == 0:
                # Initialize Kalman filter state
                self.kalman_filter.statePre = np.array([
                    ball_position[0], ball_position[1], 0, 0
                ], dtype=np.float32).reshape(4, 1)
            
            # Predict and update
            prediction = self.kalman_filter.predict()
            self.kalman_filter.correct(measurement)
            
            # Store position history
            self.previous_positions.append(ball_position)
            if len(self.previous_positions) > self.max_position_history:
                self.previous_positions.pop(0)
            
            # Return predicted position
            return (float(prediction[0]), float(prediction[1]))
            
        except Exception as e:
            logger.error(f"Error updating ball tracking: {str(e)}")
            return ball_position
    
    def _calculate_velocity(self) -> Optional[Tuple[float, float]]:
        """
        Calculate ball velocity from position history.
        
        Returns:
            Velocity tuple (vx, vy) or None if insufficient data
        """
        if len(self.previous_positions) < 2:
            return None
        
        try:
            # Calculate velocity from last two positions
            pos1 = self.previous_positions[-2]
            pos2 = self.previous_positions[-1]
            
            vx = pos2[0] - pos1[0]
            vy = pos2[1] - pos1[1]
            
            return (vx, vy)
            
        except Exception as e:
            logger.error(f"Error calculating velocity: {str(e)}")
            return None

    def _estimate_ball_height(self, frame: np.ndarray,
                             ball_position: Tuple[float, float]) -> Optional[float]:
        """
        Estimate ball height above the court.

        Args:
            frame: Input frame
            ball_position: Ball position in image coordinates

        Returns:
            Estimated height in court units or None if estimation fails
        """
        try:
            # This is a simplified height estimation
            # In a full implementation, you would use:
            # - Shadow analysis
            # - Ball size analysis
            # - Court perspective analysis
            # - Multiple camera views

            # For now, use a simple heuristic based on y-position
            frame_height = frame.shape[0]
            y_position = ball_position[1]

            # Assume ball is higher when it's higher in the frame
            # This is a very rough approximation
            normalized_y = y_position / frame_height

            # Estimate height (0-10 feet range)
            estimated_height = (1.0 - normalized_y) * 10.0

            return max(0.0, estimated_height)

        except Exception as e:
            logger.error(f"Error estimating ball height: {str(e)}")
            return None

    def _transform_to_court_coordinates(self, ball_position: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Transform ball position to court coordinates.

        Args:
            ball_position: Ball position in image coordinates

        Returns:
            Ball position in court coordinates or None if transformation fails
        """
        if self.homography_matrix is None:
            return None

        try:
            # Transform point using homography matrix
            point_homogeneous = np.array([[ball_position[0], ball_position[1], 1.0]], dtype=np.float32).T
            transformed = self.homography_matrix @ point_homogeneous

            if transformed[2, 0] != 0:
                court_x = transformed[0, 0] / transformed[2, 0]
                court_y = transformed[1, 0] / transformed[2, 0]
                return (float(court_x), float(court_y))

            return None

        except Exception as e:
            logger.error(f"Error transforming ball position to court coordinates: {str(e)}")
            return None

    def analyze_possession(self, ball_detection: BallDetection,
                          player_detections: List[Dict[str, Any]]) -> BallDetection:
        """
        Analyze ball possession based on proximity to players.

        Args:
            ball_detection: Current ball detection
            player_detections: List of player detections

        Returns:
            Updated ball detection with possession information
        """
        if not ball_detection.detected or not ball_detection.position:
            return ball_detection

        try:
            ball_x, ball_y = ball_detection.position
            closest_player = None
            closest_distance = float('inf')

            # Find closest player to the ball
            for player in player_detections:
                bbox = player['bbox']

                # Calculate player center
                player_x = (bbox[0] + bbox[2]) / 2
                player_y = (bbox[1] + bbox[3]) / 2

                # Calculate distance to ball
                distance = np.sqrt((ball_x - player_x)**2 + (ball_y - player_y)**2)

                if distance < closest_distance:
                    closest_distance = distance
                    closest_player = player

            # Determine possession based on distance threshold
            possession_threshold = 100  # pixels

            if closest_player and closest_distance < possession_threshold:
                ball_detection.possessing_player = closest_player['player_id']
                ball_detection.possessing_team = closest_player.get('team_id')
            else:
                ball_detection.possessing_player = None
                ball_detection.possessing_team = None

            return ball_detection

        except Exception as e:
            logger.error(f"Error analyzing ball possession: {str(e)}")
            return ball_detection

    def set_court_homography(self, homography_matrix: np.ndarray):
        """
        Set the court homography matrix for coordinate transformation.

        Args:
            homography_matrix: 3x3 homography transformation matrix
        """
        self.homography_matrix = homography_matrix
        logger.info("Court homography matrix set for ball detector")

    def reset_tracking(self):
        """Reset ball tracking state."""
        self.previous_positions.clear()
        if self.kalman_filter is not None:
            self.kalman_filter = self._initialize_kalman_filter()
        logger.info("Ball tracking state reset")

    def get_ball_trajectory(self) -> List[Tuple[float, float]]:
        """
        Get the recent ball trajectory.

        Returns:
            List of recent ball positions
        """
        return self.previous_positions.copy()

    def is_ball_in_motion(self, velocity_threshold: float = 5.0) -> bool:
        """
        Check if the ball is in motion based on recent velocity.

        Args:
            velocity_threshold: Minimum velocity to consider ball in motion

        Returns:
            True if ball is in motion, False otherwise
        """
        velocity = self._calculate_velocity()
        if velocity is None:
            return False

        vx, vy = velocity
        speed = np.sqrt(vx**2 + vy**2)

        return speed > velocity_threshold

    def predict_ball_position(self, frames_ahead: int = 1) -> Optional[Tuple[float, float]]:
        """
        Predict future ball position based on current trajectory.

        Args:
            frames_ahead: Number of frames to predict ahead

        Returns:
            Predicted ball position or None if prediction not possible
        """
        if len(self.previous_positions) < 2:
            return None

        try:
            velocity = self._calculate_velocity()
            if velocity is None:
                return None

            current_position = self.previous_positions[-1]
            vx, vy = velocity

            # Simple linear prediction
            predicted_x = current_position[0] + vx * frames_ahead
            predicted_y = current_position[1] + vy * frames_ahead

            return (predicted_x, predicted_y)

        except Exception as e:
            logger.error(f"Error predicting ball position: {str(e)}")
            return None
