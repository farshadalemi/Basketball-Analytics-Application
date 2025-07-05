"""
Advanced basketball court detection service using computer vision.

This module provides state-of-the-art court detection capabilities including:
- Line detection using Hough transforms
- Court corner detection and perspective correction
- Court feature recognition (three-point line, paint area, etc.)
- Homography matrix calculation for real-world coordinate mapping
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class CourtFeatures:
    """Data class for storing detected court features."""
    corners: Optional[List[Tuple[float, float]]] = None
    three_point_line: Optional[List[Tuple[float, float]]] = None
    free_throw_line: Optional[List[Tuple[float, float]]] = None
    center_circle: Optional[Dict[str, float]] = None  # {"center": [x, y], "radius": r}
    paint_area: Optional[List[Tuple[float, float]]] = None
    homography_matrix: Optional[np.ndarray] = None
    confidence_score: float = 0.0


class CourtDetector:
    """
    Advanced basketball court detection using multiple computer vision techniques.
    
    This class implements a robust court detection pipeline that can handle
    various camera angles, lighting conditions, and court types.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the court detector with configuration parameters.
        
        Args:
            config: Configuration dictionary with detection parameters
        """
        self.config = config or {}
        
        # Standard basketball court dimensions (in feet)
        self.court_length = 94.0  # NBA court length
        self.court_width = 50.0   # NBA court width
        self.three_point_distance = 23.75  # NBA three-point line distance
        self.free_throw_line_distance = 15.0
        self.key_width = 16.0
        self.key_height = 19.0
        self.center_circle_radius = 6.0
        
        # Detection parameters
        self.line_detection_params = {
            'rho': 1,
            'theta': np.pi / 180,
            'threshold': 100,
            'min_line_length': 50,
            'max_line_gap': 10
        }
        
        # Update with user config
        if 'line_detection' in self.config:
            self.line_detection_params.update(self.config['line_detection'])
    
    def detect_court(self, frame: np.ndarray) -> CourtFeatures:
        """
        Detect basketball court features in a video frame.
        
        Args:
            frame: Input video frame as numpy array (BGR format)
            
        Returns:
            CourtFeatures object containing detected court elements
        """
        try:
            logger.debug("Starting court detection")
            
            # Preprocess the frame
            processed_frame = self._preprocess_frame(frame)
            
            # Detect lines using Hough transform
            lines = self._detect_lines(processed_frame)
            
            if lines is None or len(lines) == 0:
                logger.warning("No lines detected in frame")
                return CourtFeatures(confidence_score=0.0)
            
            # Filter and classify lines
            court_lines = self._filter_court_lines(lines, frame.shape)
            
            # Detect court corners
            corners = self._detect_court_corners(court_lines, frame.shape)
            
            # Detect specific court features
            features = CourtFeatures()
            features.corners = corners
            
            if corners and len(corners) >= 4:
                # Calculate homography matrix
                features.homography_matrix = self._calculate_homography(corners)
                
                # Detect court features
                features.three_point_line = self._detect_three_point_line(processed_frame, corners)
                features.free_throw_line = self._detect_free_throw_line(processed_frame, corners)
                features.center_circle = self._detect_center_circle(processed_frame, corners)
                features.paint_area = self._detect_paint_area(processed_frame, corners)
                
                # Calculate confidence score
                features.confidence_score = self._calculate_confidence_score(features)
            
            logger.debug(f"Court detection completed with confidence: {features.confidence_score}")
            return features
            
        except Exception as e:
            logger.error(f"Error in court detection: {str(e)}")
            return CourtFeatures(confidence_score=0.0)
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess the frame for better line detection.
        
        Args:
            frame: Input frame
            
        Returns:
            Preprocessed frame optimized for line detection
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)
        
        # Edge detection using Canny
        edges = cv2.Canny(enhanced, 50, 150, apertureSize=3)
        
        # Morphological operations to connect broken lines
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        return edges
    
    def _detect_lines(self, processed_frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect lines using probabilistic Hough transform.
        
        Args:
            processed_frame: Preprocessed frame with edges
            
        Returns:
            Array of detected lines or None if no lines found
        """
        lines = cv2.HoughLinesP(
            processed_frame,
            rho=self.line_detection_params['rho'],
            theta=self.line_detection_params['theta'],
            threshold=self.line_detection_params['threshold'],
            minLineLength=self.line_detection_params['min_line_length'],
            maxLineGap=self.line_detection_params['max_line_gap']
        )
        
        return lines
    
    def _filter_court_lines(self, lines: np.ndarray, frame_shape: Tuple[int, int, int]) -> List[Tuple[float, float, float, float]]:
        """
        Filter and classify detected lines to identify court boundaries.
        
        Args:
            lines: Raw detected lines
            frame_shape: Shape of the input frame
            
        Returns:
            List of filtered court lines
        """
        if lines is None:
            return []
        
        height, width = frame_shape[:2]
        court_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Calculate line length and angle
            length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            
            # Filter lines based on length and position
            if length > min(width, height) * 0.1:  # Minimum length threshold
                # Normalize angle to 0-180 range
                angle = abs(angle)
                if angle > 90:
                    angle = 180 - angle
                
                # Keep lines that are roughly horizontal or vertical
                if angle < 15 or angle > 75:  # Allow some tolerance
                    court_lines.append((x1, y1, x2, y2))
        
        return court_lines
    
    def _detect_court_corners(self, lines: List[Tuple[float, float, float, float]], 
                            frame_shape: Tuple[int, int, int]) -> Optional[List[Tuple[float, float]]]:
        """
        Detect court corners from filtered lines.
        
        Args:
            lines: Filtered court lines
            frame_shape: Shape of the input frame
            
        Returns:
            List of detected corner points or None if insufficient corners found
        """
        if len(lines) < 4:
            return None
        
        height, width = frame_shape[:2]
        corners = []
        
        # Find intersections between lines
        for i, line1 in enumerate(lines):
            for j, line2 in enumerate(lines[i+1:], i+1):
                intersection = self._line_intersection(line1, line2)
                if intersection:
                    x, y = intersection
                    # Check if intersection is within frame bounds
                    if 0 <= x <= width and 0 <= y <= height:
                        corners.append((x, y))
        
        if len(corners) < 4:
            return None
        
        # Sort corners to form a quadrilateral
        corners = self._sort_corners(corners)
        
        # Return the 4 most likely court corners
        return corners[:4] if len(corners) >= 4 else None
    
    def _line_intersection(self, line1: Tuple[float, float, float, float], 
                          line2: Tuple[float, float, float, float]) -> Optional[Tuple[float, float]]:
        """
        Calculate intersection point of two lines.
        
        Args:
            line1: First line (x1, y1, x2, y2)
            line2: Second line (x1, y1, x2, y2)
            
        Returns:
            Intersection point (x, y) or None if lines are parallel
        """
        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2
        
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:  # Lines are parallel
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        
        return (x, y)
    
    def _sort_corners(self, corners: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Sort corners in clockwise order starting from top-left.
        
        Args:
            corners: List of corner points
            
        Returns:
            Sorted list of corners
        """
        # Convert to numpy array for easier manipulation
        corners_array = np.array(corners)
        
        # Find centroid
        centroid = np.mean(corners_array, axis=0)
        
        # Calculate angles from centroid
        angles = np.arctan2(corners_array[:, 1] - centroid[1], 
                           corners_array[:, 0] - centroid[0])
        
        # Sort by angle
        sorted_indices = np.argsort(angles)
        sorted_corners = corners_array[sorted_indices]
        
        return [(float(x), float(y)) for x, y in sorted_corners]

    def _calculate_homography(self, corners: List[Tuple[float, float]]) -> Optional[np.ndarray]:
        """
        Calculate homography matrix for perspective transformation.

        Args:
            corners: Detected court corners

        Returns:
            3x3 homography matrix or None if calculation fails
        """
        if len(corners) < 4:
            return None

        try:
            # Source points (detected corners)
            src_points = np.array(corners[:4], dtype=np.float32)

            # Destination points (standard court rectangle)
            dst_points = np.array([
                [0, 0],                    # Top-left
                [self.court_width, 0],     # Top-right
                [self.court_width, self.court_length],  # Bottom-right
                [0, self.court_length]     # Bottom-left
            ], dtype=np.float32)

            # Calculate homography matrix
            homography_matrix = cv2.getPerspectiveTransform(src_points, dst_points)

            return homography_matrix

        except Exception as e:
            logger.error(f"Error calculating homography: {str(e)}")
            return None

    def _detect_three_point_line(self, processed_frame: np.ndarray,
                                corners: List[Tuple[float, float]]) -> Optional[List[Tuple[float, float]]]:
        """
        Detect three-point line using template matching and curve detection.

        Args:
            processed_frame: Preprocessed frame
            corners: Detected court corners

        Returns:
            List of points forming the three-point line
        """
        # This is a simplified implementation
        # In a full implementation, you would use more sophisticated curve detection
        try:
            # Use HoughCircles to detect circular arcs
            circles = cv2.HoughCircles(
                processed_frame,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=100,
                param1=50,
                param2=30,
                minRadius=50,
                maxRadius=200
            )

            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                # Return the largest circle as potential three-point arc
                if len(circles) > 0:
                    # Convert circle to points
                    center_x, center_y, radius = circles[0]
                    points = []
                    for angle in range(0, 180, 5):  # Half circle
                        x = center_x + radius * np.cos(np.radians(angle))
                        y = center_y + radius * np.sin(np.radians(angle))
                        points.append((float(x), float(y)))
                    return points

            return None

        except Exception as e:
            logger.error(f"Error detecting three-point line: {str(e)}")
            return None

    def _detect_free_throw_line(self, processed_frame: np.ndarray,
                               corners: List[Tuple[float, float]]) -> Optional[List[Tuple[float, float]]]:
        """
        Detect free throw line.

        Args:
            processed_frame: Preprocessed frame
            corners: Detected court corners

        Returns:
            List of points forming the free throw line
        """
        # Simplified implementation - would need more sophisticated detection
        # For now, return None to indicate feature not implemented
        return None

    def _detect_center_circle(self, processed_frame: np.ndarray,
                             corners: List[Tuple[float, float]]) -> Optional[Dict[str, float]]:
        """
        Detect center circle of the court.

        Args:
            processed_frame: Preprocessed frame
            corners: Detected court corners

        Returns:
            Dictionary with center coordinates and radius
        """
        try:
            # Use HoughCircles to detect the center circle
            circles = cv2.HoughCircles(
                processed_frame,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=50,
                param1=50,
                param2=30,
                minRadius=20,
                maxRadius=100
            )

            if circles is not None:
                circles = np.round(circles[0, :]).astype("int")
                if len(circles) > 0:
                    # Return the first detected circle
                    center_x, center_y, radius = circles[0]
                    return {
                        "center": [float(center_x), float(center_y)],
                        "radius": float(radius)
                    }

            return None

        except Exception as e:
            logger.error(f"Error detecting center circle: {str(e)}")
            return None

    def _detect_paint_area(self, processed_frame: np.ndarray,
                          corners: List[Tuple[float, float]]) -> Optional[List[Tuple[float, float]]]:
        """
        Detect paint area (key) of the court.

        Args:
            processed_frame: Preprocessed frame
            corners: Detected court corners

        Returns:
            List of points forming the paint area polygon
        """
        # Simplified implementation - would need more sophisticated detection
        # For now, return None to indicate feature not implemented
        return None

    def _calculate_confidence_score(self, features: CourtFeatures) -> float:
        """
        Calculate confidence score for court detection.

        Args:
            features: Detected court features

        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.0

        # Base score for having corners
        if features.corners and len(features.corners) >= 4:
            score += 0.4

        # Additional score for homography matrix
        if features.homography_matrix is not None:
            score += 0.2

        # Score for detected features
        if features.three_point_line:
            score += 0.15
        if features.center_circle:
            score += 0.15
        if features.free_throw_line:
            score += 0.05
        if features.paint_area:
            score += 0.05

        return min(score, 1.0)

    def transform_point_to_court_coordinates(self, point: Tuple[float, float],
                                           homography_matrix: np.ndarray) -> Optional[Tuple[float, float]]:
        """
        Transform a point from image coordinates to court coordinates.

        Args:
            point: Point in image coordinates (x, y)
            homography_matrix: Homography transformation matrix

        Returns:
            Point in court coordinates or None if transformation fails
        """
        try:
            # Convert point to homogeneous coordinates
            point_homogeneous = np.array([[point[0], point[1], 1.0]], dtype=np.float32).T

            # Apply transformation
            transformed = homography_matrix @ point_homogeneous

            # Convert back to Cartesian coordinates
            if transformed[2, 0] != 0:
                x = transformed[0, 0] / transformed[2, 0]
                y = transformed[1, 0] / transformed[2, 0]
                return (float(x), float(y))

            return None

        except Exception as e:
            logger.error(f"Error transforming point: {str(e)}")
            return None
