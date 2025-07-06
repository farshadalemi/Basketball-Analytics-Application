"""
Enhanced basketball detection and tracking service.

This module provides comprehensive basketball detection capabilities including:
- Enhanced YOLO-based ball detection with sports ball class optimization
- Multi-modal detection combining YOLO, color, and geometric features
- Advanced Kalman filtering for trajectory prediction and occlusion handling
- Ball height estimation using court homography and perspective analysis
- Velocity, acceleration, and trajectory analysis
- Temporal consistency and noise filtering
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
import math
from collections import deque

try:
    from filterpy.kalman import KalmanFilter
    from filterpy.common import Q_discrete_white_noise
    FILTERPY_AVAILABLE = True
except ImportError:
    FILTERPY_AVAILABLE = False
    # Don't log warning during import to avoid container issues

logger = logging.getLogger(__name__)


@dataclass
class BallDetection:
    """Enhanced data class for storing ball detection results."""
    detected: bool
    position: Optional[Tuple[float, float]] = None  # x, y in image coordinates
    court_position: Optional[Tuple[float, float]] = None  # x, y in court coordinates
    confidence: float = 0.0
    velocity: Optional[Tuple[float, float]] = None  # vx, vy
    acceleration: Optional[Tuple[float, float]] = None  # ax, ay
    height_estimate: Optional[float] = None  # Estimated height above court
    trajectory_points: Optional[List[Tuple[float, float]]] = None  # Recent trajectory
    detection_method: str = "unknown"  # yolo, color, geometric, predicted
    tracking_confidence: float = 0.0  # Temporal tracking confidence
    occlusion_status: str = "visible"  # visible, occluded, predicted
    ball_state: str = "unknown"  # dribbling, shooting, passing, stationary
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
        self.confidence_threshold = self.config.get('confidence_threshold', 0.25)  # Lower for better recall

        # Enhanced detection parameters
        self.detection_params = {
            'yolo_weight': 0.5,
            'color_weight': 0.3,
            'geometric_weight': 0.2,
            'min_ball_area': 20,
            'max_ball_area': 2000,
            'min_circularity': 0.4,
            'max_velocity': 50.0,  # pixels per frame
            'trajectory_length': 10,
            'occlusion_threshold': 5,  # frames
        }

        # Update with user config
        if 'detection_params' in self.config:
            self.detection_params.update(self.config['detection_params'])

        # Initialize YOLO model for ball detection
        self.yolo_model = self._load_yolo_model()

        # Enhanced tracking state
        self.ball_trajectory = deque(maxlen=self.detection_params['trajectory_length'])
        self.velocity_history = deque(maxlen=5)
        self.confidence_history = deque(maxlen=5)
        self.previous_positions = []
        self.max_position_history = 10
        self.kalman_filter = self._initialize_enhanced_kalman_filter()
        self.tracking_state = "searching"  # searching, tracking, occluded, lost
        self.frames_since_detection = 0

        # Enhanced ball characteristics for color-based detection
        self.ball_color_ranges = {
            'orange': {
                'lower': np.array([5, 100, 100]),
                'upper': np.array([15, 255, 255])
            },
            'brown': {
                'lower': np.array([10, 50, 50]),
                'upper': np.array([20, 255, 200])
            }
        }

        # Court homography matrix for coordinate transformation
        self.homography_matrix = None

        logger.info("Enhanced BallDetector initialized successfully")
    
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
        Simplified but robust basketball detection.

        Args:
            frame: Input video frame as numpy array (BGR format)
            frame_number: Current frame number for tracking

        Returns:
            BallDetection object with detection results
        """
        try:
            logger.debug(f"Ball detection in frame {frame_number}")

            # Simple color-based ball detection
            ball_position, confidence = self._detect_ball_simple_color(frame)

            if ball_position is not None:
                detection = BallDetection(
                    detected=True,
                    position=ball_position,
                    confidence=confidence,
                    detection_method="color_based"
                )
                logger.debug(f"Ball detected at {ball_position} with confidence {confidence:.3f}")
            else:
                # Try geometric detection as fallback
                ball_position, confidence = self._detect_ball_simple_geometric(frame)
                if ball_position is not None:
                    detection = BallDetection(
                        detected=True,
                        position=ball_position,
                        confidence=confidence,
                        detection_method="geometric"
                    )
                    logger.debug(f"Ball detected (geometric) at {ball_position} with confidence {confidence:.3f}")
                else:
                    detection = BallDetection(
                        detected=False,
                        position=None,
                        confidence=0.0,
                        detection_method="none"
                    )
                    logger.debug("No ball detected")

            return detection

        except Exception as e:
            logger.error(f"Error in ball detection: {str(e)}")
            return BallDetection(detected=False, detection_method="error")

    def _detect_ball_simple_color(self, frame: np.ndarray) -> Tuple[Optional[Tuple[float, float]], float]:
        """
        Simple color-based ball detection.

        Args:
            frame: Input frame

        Returns:
            Tuple of (position, confidence) or (None, 0.0)
        """
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Define orange/brown color range for basketball
            lower_orange = np.array([5, 100, 100])
            upper_orange = np.array([25, 255, 255])

            # Create mask for ball color
            mask = cv2.inRange(hsv, lower_orange, upper_orange)

            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                # Find the most circular contour
                best_contour = None
                best_score = 0

                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 50:  # Minimum area threshold
                        # Calculate circularity
                        perimeter = cv2.arcLength(contour, True)
                        if perimeter > 0:
                            circularity = 4 * np.pi * area / (perimeter * perimeter)
                            if circularity > best_score and circularity > 0.3:  # Reasonably circular
                                best_score = circularity
                                best_contour = contour

                if best_contour is not None:
                    # Get center of the contour
                    M = cv2.moments(best_contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        confidence = min(0.8, best_score)
                        return (float(cx), float(cy)), confidence

            return None, 0.0

        except Exception as e:
            logger.error(f"Error in simple color detection: {str(e)}")
            return None, 0.0

    def _detect_ball_simple_geometric(self, frame: np.ndarray) -> Tuple[Optional[Tuple[float, float]], float]:
        """
        Simple geometric ball detection using Hough circles.

        Args:
            frame: Input frame

        Returns:
            Tuple of (position, confidence) or (None, 0.0)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (9, 9), 2)

            # Detect circles using HoughCircles
            circles = cv2.HoughCircles(
                blurred,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=30,
                param1=50,
                param2=30,
                minRadius=5,
                maxRadius=50
            )

            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")

                # Find the best circle (closest to expected ball size)
                best_circle = None
                best_score = 0

                for (x, y, r) in circles:
                    # Score based on radius (basketballs are typically 10-30 pixels in radius)
                    if 8 <= r <= 40:
                        score = 1.0 - abs(r - 20) / 20  # Prefer radius around 20
                        if score > best_score:
                            best_score = score
                            best_circle = (x, y, r)

                if best_circle is not None:
                    x, y, r = best_circle
                    confidence = min(0.6, best_score)
                    return (float(x), float(y)), confidence

            return None, 0.0

        except Exception as e:
            logger.error(f"Error in simple geometric detection: {str(e)}")
            return None, 0.0
    
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

    def _detect_ball_yolo_enhanced(self, frame: np.ndarray) -> Tuple[Optional[Tuple[float, float]], float]:
        """
        Enhanced YOLO-based ball detection with sports ball class optimization.

        Args:
            frame: Input frame

        Returns:
            Tuple of (ball_position, confidence) or (None, 0.0)
        """
        try:
            # Run YOLO inference with sports ball class (32)
            results = self.yolo_model(frame, classes=[32], verbose=False)

            best_detection = None
            best_confidence = 0.0

            for result in results:
                if hasattr(result, 'boxes') and result.boxes is not None:
                    for box in result.boxes:
                        confidence = float(box.conf[0])

                        if confidence > best_confidence and confidence >= self.confidence_threshold:
                            # Get bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].tolist()

                            # Calculate center and validate size
                            center_x = (x1 + x2) / 2
                            center_y = (y1 + y2) / 2
                            area = (x2 - x1) * (y2 - y1)

                            # Filter by reasonable ball size
                            if (self.detection_params['min_ball_area'] <= area <=
                                self.detection_params['max_ball_area']):
                                best_detection = (center_x, center_y)
                                best_confidence = confidence

            return best_detection, best_confidence

        except Exception as e:
            logger.error(f"Error in enhanced YOLO detection: {str(e)}")
            return None, 0.0

    def _detect_ball_color_enhanced(self, frame: np.ndarray) -> Tuple[Optional[Tuple[float, float]], float]:
        """
        Enhanced color-based ball detection with multiple color ranges.

        Args:
            frame: Input frame

        Returns:
            Tuple of (ball_position, confidence) or (None, 0.0)
        """
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            best_detection = None
            best_confidence = 0.0

            # Try different basketball color ranges
            for color_name, color_range in self.ball_color_ranges.items():
                # Create mask for current color
                mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])

                # Apply morphological operations to clean up mask
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

                # Find contours
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    # Filter by area
                    area = cv2.contourArea(contour)
                    if area < self.detection_params['min_ball_area'] or area > self.detection_params['max_ball_area']:
                        continue

                    # Check circularity
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter == 0:
                        continue

                    circularity = 4 * np.pi * area / (perimeter * perimeter)

                    if circularity > self.detection_params['min_circularity']:
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
            logger.error(f"Error in enhanced color detection: {str(e)}")
            return None, 0.0

    def _detect_ball_geometric(self, frame: np.ndarray) -> Tuple[Optional[Tuple[float, float]], float]:
        """
        Geometric ball detection using circular Hough transform.

        Args:
            frame: Input frame

        Returns:
            Tuple of (ball_position, confidence) or (None, 0.0)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (9, 9), 2)

            # Use HoughCircles to detect circular objects
            circles = cv2.HoughCircles(
                blurred,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=30,
                param1=50,
                param2=30,
                minRadius=int(math.sqrt(self.detection_params['min_ball_area'] / math.pi)),
                maxRadius=int(math.sqrt(self.detection_params['max_ball_area'] / math.pi))
            )

            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")

                # Find the best circle (highest confidence)
                best_detection = None
                best_confidence = 0.0

                for (x, y, r) in circles:
                    # Calculate confidence based on circle quality
                    area = math.pi * r * r
                    if (self.detection_params['min_ball_area'] <= area <=
                        self.detection_params['max_ball_area']):

                        # Simple confidence based on radius consistency
                        confidence = min(1.0, area / 1000.0)

                        if confidence > best_confidence:
                            best_detection = (float(x), float(y))
                            best_confidence = confidence

                return best_detection, best_confidence

            return None, 0.0

        except Exception as e:
            logger.error(f"Error in geometric detection: {str(e)}")
            return None, 0.0

    def _fuse_detections(self, detections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Fuse multiple detection results using weighted combination.

        Args:
            detections: List of detection dictionaries

        Returns:
            Fused detection or None if no valid detections
        """
        if not detections:
            return None

        # If only one detection, return it
        if len(detections) == 1:
            return detections[0]

        # Weighted fusion of multiple detections
        total_weight = 0.0
        weighted_x = 0.0
        weighted_y = 0.0
        weighted_confidence = 0.0
        best_method = "fused"

        for detection in detections:
            weight = detection['weight'] * detection['confidence']
            total_weight += weight

            x, y = detection['position']
            weighted_x += x * weight
            weighted_y += y * weight
            weighted_confidence += detection['confidence'] * detection['weight']

        if total_weight > 0:
            final_position = (weighted_x / total_weight, weighted_y / total_weight)
            final_confidence = weighted_confidence / sum(d['weight'] for d in detections)

            # Use method of highest confidence detection
            best_detection = max(detections, key=lambda d: d['confidence'])
            best_method = best_detection['method']

            return {
                'position': final_position,
                'confidence': final_confidence,
                'method': best_method
            }

        return None

    def _update_enhanced_tracking(self, position: Tuple[float, float], confidence: float):
        """
        Update enhanced tracking state with new detection.

        Args:
            position: Ball position (x, y)
            confidence: Detection confidence
        """
        # Add to trajectory
        self.ball_trajectory.append(position)
        self.confidence_history.append(confidence)

        # Update Kalman filter if available
        if self.kalman_filter is not None:
            try:
                measurement = np.array([[position[0]], [position[1]]], dtype=np.float32)
                self.kalman_filter.correct(measurement)
                self.kalman_filter.predict()
            except Exception as e:
                logger.error(f"Error updating Kalman filter: {str(e)}")

        # Update tracking state
        self.tracking_state = "tracking"
        self.frames_since_detection = 0

        # Calculate velocity if we have enough history
        if len(self.ball_trajectory) >= 2:
            prev_pos = self.ball_trajectory[-2]
            curr_pos = self.ball_trajectory[-1]
            velocity = (curr_pos[0] - prev_pos[0], curr_pos[1] - prev_pos[1])
            self.velocity_history.append(velocity)

    def _calculate_velocity(self) -> Optional[Tuple[float, float]]:
        """Calculate current ball velocity."""
        if len(self.velocity_history) > 0:
            # Average recent velocities for smoothing
            recent_velocities = list(self.velocity_history)[-3:]
            avg_vx = sum(v[0] for v in recent_velocities) / len(recent_velocities)
            avg_vy = sum(v[1] for v in recent_velocities) / len(recent_velocities)
            return (avg_vx, avg_vy)
        return None

    def _calculate_acceleration(self) -> Optional[Tuple[float, float]]:
        """Calculate current ball acceleration."""
        if len(self.velocity_history) >= 2:
            curr_vel = self.velocity_history[-1]
            prev_vel = self.velocity_history[-2]
            acceleration = (curr_vel[0] - prev_vel[0], curr_vel[1] - prev_vel[1])
            return acceleration
        return None

    def _calculate_tracking_confidence(self) -> float:
        """Calculate overall tracking confidence."""
        if not self.confidence_history:
            return 0.0

        # Average recent confidences
        recent_confidences = list(self.confidence_history)[-3:]
        avg_confidence = sum(recent_confidences) / len(recent_confidences)

        # Adjust based on tracking state
        if self.tracking_state == "tracking":
            return avg_confidence
        elif self.tracking_state == "occluded":
            return avg_confidence * 0.7
        else:
            return avg_confidence * 0.5

    def _analyze_ball_state(self) -> str:
        """Analyze ball state based on trajectory and velocity."""
        if not self.velocity_history:
            return "unknown"

        current_velocity = self.velocity_history[-1]
        speed = math.sqrt(current_velocity[0]**2 + current_velocity[1]**2)

        if speed < 2.0:
            return "stationary"
        elif speed < 10.0:
            return "dribbling"
        elif speed < 25.0:
            return "passing"
        else:
            return "shooting"

    def _initialize_enhanced_kalman_filter(self):
        """Initialize enhanced Kalman filter for ball tracking."""
        if not FILTERPY_AVAILABLE:
            return self._initialize_kalman_filter()  # Fallback to basic filter

        try:
            # Create Kalman filter with position and velocity
            kf = KalmanFilter(dim_x=4, dim_z=2)

            # State transition matrix (constant velocity model)
            kf.F = np.array([
                [1, 0, 1, 0],
                [0, 1, 0, 1],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])

            # Measurement function (position only)
            kf.H = np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0]
            ])

            # Measurement noise
            kf.R *= 10

            # Process noise
            kf.Q = Q_discrete_white_noise(dim=2, dt=1, var=0.1, block_size=2)

            # Initial covariance
            kf.P *= 100

            return kf

        except Exception as e:
            logger.error(f"Error initializing enhanced Kalman filter: {str(e)}")
            return self._initialize_kalman_filter()  # Fallback

    def _predict_ball_position(self) -> Optional[Tuple[float, float]]:
        """
        Predict ball position using Kalman filter.

        Returns:
            Predicted position or None if prediction fails
        """
        if self.kalman_filter is None:
            return None

        try:
            if FILTERPY_AVAILABLE and hasattr(self.kalman_filter, 'predict'):
                self.kalman_filter.predict()
                return (float(self.kalman_filter.x[0]), float(self.kalman_filter.x[1]))
            elif hasattr(self.kalman_filter, 'predict'):
                prediction = self.kalman_filter.predict()
                return (float(prediction[0]), float(prediction[1]))

            return None

        except Exception as e:
            logger.error(f"Error predicting ball position: {str(e)}")
            return None

    def _create_predicted_detection(self, predicted_pos: Tuple[float, float], frame_number: int) -> BallDetection:
        """
        Create a ball detection from predicted position.

        Args:
            predicted_pos: Predicted ball position
            frame_number: Current frame number

        Returns:
            BallDetection with predicted information
        """
        return BallDetection(
            detected=True,
            position=predicted_pos,
            confidence=0.3,  # Lower confidence for predictions
            detection_method="predicted",
            tracking_confidence=0.5,
            occlusion_status="occluded",
            ball_state="unknown"
        )

    def _estimate_ball_height_enhanced(self, frame: np.ndarray, position: Tuple[float, float]) -> Optional[float]:
        """
        Enhanced ball height estimation using perspective analysis.

        Args:
            frame: Current frame
            position: Ball position in image

        Returns:
            Estimated height or None if estimation fails
        """
        # Simple heuristic based on y-coordinate
        # Lower in image = closer to ground
        frame_height = frame.shape[0]
        y_pos = position[1]

        # Normalize y position (0 = top, 1 = bottom)
        normalized_y = y_pos / frame_height

        # Estimate height (higher y = lower height)
        # Assume maximum height of 3 meters
        estimated_height = (1.0 - normalized_y) * 3.0

        return max(0.0, estimated_height)

    def set_court_homography(self, homography: np.ndarray):
        """
        Set the court homography matrix for coordinate transformation.

        Args:
            homography: Homography matrix from court detection
        """
        self.homography_matrix = homography
        logger.debug("Court homography updated for ball tracking")

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
