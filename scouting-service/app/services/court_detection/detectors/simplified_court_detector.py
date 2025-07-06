"""
Enhanced Basketball Court Detection with Adaptive Multi-Method Approach.

This module provides an advanced court detection system that combines:
- CNN-based keypoint detection
- Adaptive parameter tuning
- Multi-method line detection fusion
- Temporal consistency
- Homography-based court mapping
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
import logging
import time
import os
from dataclasses import dataclass
from collections import deque
import math

# Import CNN-based basketball court detection
try:
    from .basketball_court_keypoints import BasketballCourtKeypointDetector, BasketballCourtKeypoints, BasketballCourtTemplate
    CNN_DETECTION_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CNN-based court detection not available: {e}")
    CNN_DETECTION_AVAILABLE = False
    # Create dummy classes for when PyTorch is not available
    class BasketballCourtKeypoints:
        def __init__(self, keypoints, confidence, detection_method="unavailable"):
            self.keypoints = keypoints
            self.confidence = confidence
            self.detection_method = detection_method

    class BasketballCourtTemplate:
        @classmethod
        def get_keypoint_names(cls):
            return ["dummy"] * 14

logger = logging.getLogger(__name__)


class LightingConditionAnalyzer:
    """Analyzes image lighting conditions for adaptive parameter tuning."""

    def __init__(self):
        self.brightness_thresholds = {
            'very_dark': 30,
            'dark': 60,
            'normal': 150,
            'bright': 200
        }
        self.contrast_thresholds = {
            'very_low': 15,
            'low': 30,
            'normal': 60,
            'high': 100
        }

    def analyze(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze lighting conditions of the image."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # Calculate brightness metrics
        brightness = np.mean(gray)
        brightness_std = np.std(gray)

        # Calculate contrast metrics
        contrast = np.std(gray)

        # Determine lighting condition
        if brightness < self.brightness_thresholds['very_dark']:
            lighting_level = 'very_dark'
        elif brightness < self.brightness_thresholds['dark']:
            lighting_level = 'dark'
        elif brightness < self.brightness_thresholds['normal']:
            lighting_level = 'normal'
        elif brightness < self.brightness_thresholds['bright']:
            lighting_level = 'bright'
        else:
            lighting_level = 'very_bright'

        # Determine contrast level
        if contrast < self.contrast_thresholds['very_low']:
            contrast_level = 'very_low'
        elif contrast < self.contrast_thresholds['low']:
            contrast_level = 'low'
        elif contrast < self.contrast_thresholds['normal']:
            contrast_level = 'normal'
        elif contrast < self.contrast_thresholds['high']:
            contrast_level = 'high'
        else:
            contrast_level = 'very_high'

        return {
            'brightness': brightness,
            'brightness_std': brightness_std,
            'contrast': contrast,
            'lighting_level': lighting_level,
            'contrast_level': contrast_level,
            'uniformity': 1.0 - (brightness_std / max(brightness, 1))
        }


class AdaptiveParameterTuner:
    """Dynamically adjusts detection parameters based on image characteristics."""

    def __init__(self):
        self.lighting_analyzer = LightingConditionAnalyzer()
        self.parameter_profiles = self._initialize_parameter_profiles()

    def _initialize_parameter_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Initialize parameter profiles for different conditions."""
        return {
            'very_dark': {
                'canny_low': 30, 'canny_high': 90,
                'hough_threshold': 60, 'min_line_length': 30, 'max_line_gap': 15,
                'blur_kernel': 7, 'morph_kernel': 5
            },
            'dark': {
                'canny_low': 40, 'canny_high': 120,
                'hough_threshold': 80, 'min_line_length': 40, 'max_line_gap': 12,
                'blur_kernel': 5, 'morph_kernel': 3
            },
            'normal': {
                'canny_low': 50, 'canny_high': 150,
                'hough_threshold': 100, 'min_line_length': 50, 'max_line_gap': 10,
                'blur_kernel': 5, 'morph_kernel': 3
            },
            'bright': {
                'canny_low': 60, 'canny_high': 180,
                'hough_threshold': 120, 'min_line_length': 60, 'max_line_gap': 8,
                'blur_kernel': 3, 'morph_kernel': 3
            },
            'very_bright': {
                'canny_low': 80, 'canny_high': 200,
                'hough_threshold': 140, 'min_line_length': 70, 'max_line_gap': 6,
                'blur_kernel': 3, 'morph_kernel': 2
            }
        }

    def adapt_parameters(self, image: np.ndarray, detection_history: Optional[List] = None) -> Dict[str, Any]:
        """Adapt parameters based on image characteristics and detection history."""
        # Analyze current image
        lighting_analysis = self.lighting_analyzer.analyze(image)

        # Get base parameters for lighting condition
        base_params = self.parameter_profiles[lighting_analysis['lighting_level']].copy()

        # Adjust based on contrast level
        contrast_multiplier = self._get_contrast_multiplier(lighting_analysis['contrast_level'])
        base_params['canny_low'] = int(base_params['canny_low'] * contrast_multiplier)
        base_params['canny_high'] = int(base_params['canny_high'] * contrast_multiplier)

        # Adjust based on detection history if available
        if detection_history:
            base_params = self._adjust_from_history(base_params, detection_history)

        # Add adaptive thresholding parameters
        base_params.update({
            'adaptive_threshold_method': self._select_threshold_method(lighting_analysis),
            'adaptive_block_size': self._select_block_size(lighting_analysis),
            'adaptive_c': self._select_adaptive_c(lighting_analysis)
        })

        return base_params

    def _get_contrast_multiplier(self, contrast_level: str) -> float:
        """Get multiplier for contrast adjustment."""
        multipliers = {
            'very_low': 0.7,
            'low': 0.85,
            'normal': 1.0,
            'high': 1.15,
            'very_high': 1.3
        }
        return multipliers.get(contrast_level, 1.0)

    def _select_threshold_method(self, lighting_analysis: Dict[str, Any]) -> int:
        """Select best adaptive thresholding method."""
        if lighting_analysis['lighting_level'] in ['very_dark', 'dark']:
            return cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        elif lighting_analysis['contrast_level'] in ['very_low', 'low']:
            return cv2.THRESH_OTSU
        else:
            return cv2.ADAPTIVE_THRESH_MEAN_C

    def _select_block_size(self, lighting_analysis: Dict[str, Any]) -> int:
        """Select adaptive block size based on image characteristics."""
        if lighting_analysis['lighting_level'] in ['very_dark', 'dark']:
            return 15
        elif lighting_analysis['contrast_level'] in ['very_low', 'low']:
            return 11
        else:
            return 9

    def _select_adaptive_c(self, lighting_analysis: Dict[str, Any]) -> int:
        """Select adaptive C parameter."""
        if lighting_analysis['lighting_level'] in ['very_dark', 'dark']:
            return 8
        elif lighting_analysis['contrast_level'] in ['very_low', 'low']:
            return 5
        else:
            return 2

    def _adjust_from_history(self, params: Dict[str, Any], history: List) -> Dict[str, Any]:
        """Adjust parameters based on detection history."""
        # Simple adjustment based on recent detection success
        recent_confidences = [h.get('confidence', 0) for h in history[-3:]]
        avg_confidence = np.mean(recent_confidences) if recent_confidences else 0

        if avg_confidence < 0.3:
            # Lower thresholds for better detection
            params['canny_low'] = max(20, int(params['canny_low'] * 0.8))
            params['hough_threshold'] = max(40, int(params['hough_threshold'] * 0.8))
        elif avg_confidence > 0.8:
            # Raise thresholds to reduce noise
            params['canny_high'] = min(250, int(params['canny_high'] * 1.1))
            params['hough_threshold'] = min(200, int(params['hough_threshold'] * 1.1))

        return params


class AdaptiveLineDetector:
    """Multi-method line detection with adaptive parameters."""

    def __init__(self):
        self.methods = {
            'hough_standard': self._hough_standard,
            'hough_probabilistic': self._hough_probabilistic,
            'lsd': self._line_segment_detector,
            'contour_based': self._contour_line_detection
        }

    def detect_lines(self, image: np.ndarray, params: Dict[str, Any]) -> List[np.ndarray]:
        """Detect lines using multiple methods and fuse results."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

        # Preprocessing with adaptive parameters
        processed_image = self._preprocess_image(gray, params)

        # Multi-method line detection
        all_lines = []
        for method_name, method_func in self.methods.items():
            try:
                lines = method_func(processed_image, params)
                if lines is not None and len(lines) > 0:
                    validated_lines = self._validate_lines(lines, image.shape)
                    all_lines.extend(validated_lines)
            except Exception as e:
                logger.warning(f"Line detection method {method_name} failed: {e}")

        # Fusion and filtering
        return self._fuse_and_filter_lines(all_lines, image.shape)

    def _preprocess_image(self, gray: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Preprocess image with adaptive parameters."""
        # Adaptive Gaussian blur
        blur_kernel = params.get('blur_kernel', 5)
        blurred = cv2.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)

        # Adaptive thresholding
        if params.get('adaptive_threshold_method') == cv2.THRESH_OTSU:
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            thresh = cv2.adaptiveThreshold(
                blurred, 255,
                params.get('adaptive_threshold_method', cv2.ADAPTIVE_THRESH_MEAN_C),
                cv2.THRESH_BINARY,
                params.get('adaptive_block_size', 9),
                params.get('adaptive_c', 2)
            )

        # Morphological operations
        morph_kernel = params.get('morph_kernel', 3)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_kernel, morph_kernel))
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        return processed

    def _hough_standard(self, image: np.ndarray, params: Dict[str, Any]) -> Optional[np.ndarray]:
        """Standard Hough Transform line detection."""
        edges = cv2.Canny(image, params['canny_low'], params['canny_high'])
        lines = cv2.HoughLines(edges, 1, np.pi/180, params['hough_threshold'])

        if lines is not None:
            # Convert to line segments
            line_segments = []
            h, w = image.shape
            for line in lines:
                rho, theta = line[0]
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a * rho
                y0 = b * rho
                x1 = int(x0 + w * (-b))
                y1 = int(y0 + w * (a))
                x2 = int(x0 - w * (-b))
                y2 = int(y0 - w * (a))
                line_segments.append([[x1, y1, x2, y2]])
            return np.array(line_segments)
        return None

    def _hough_probabilistic(self, image: np.ndarray, params: Dict[str, Any]) -> Optional[np.ndarray]:
        """Probabilistic Hough Transform line detection."""
        edges = cv2.Canny(image, params['canny_low'], params['canny_high'])
        return cv2.HoughLinesP(
            edges, 1, np.pi/180,
            threshold=params['hough_threshold'],
            minLineLength=params['min_line_length'],
            maxLineGap=params['max_line_gap']
        )

    def _line_segment_detector(self, image: np.ndarray, params: Dict[str, Any]) -> Optional[np.ndarray]:
        """Line Segment Detector (LSD) method."""
        try:
            lsd = cv2.createLineSegmentDetector()
            lines = lsd.detect(image)[0]
            if lines is not None:
                return lines.reshape(-1, 1, 4).astype(int)
        except Exception as e:
            logger.warning(f"LSD detection failed: {e}")
        return None

    def _contour_line_detection(self, image: np.ndarray, params: Dict[str, Any]) -> Optional[np.ndarray]:
        """Contour-based line detection."""
        edges = cv2.Canny(image, params['canny_low'], params['canny_high'])
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        lines = []
        for contour in contours:
            # Approximate contour to lines
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) >= 2:
                for i in range(len(approx) - 1):
                    pt1 = approx[i][0]
                    pt2 = approx[i + 1][0]
                    lines.append([[pt1[0], pt1[1], pt2[0], pt2[1]]])

        return np.array(lines) if lines else None

    def _validate_lines(self, lines: np.ndarray, image_shape: Tuple[int, int]) -> List[np.ndarray]:
        """Validate and filter detected lines."""
        if lines is None or len(lines) == 0:
            return []

        h, w = image_shape[:2]
        valid_lines = []

        for line in lines:
            try:
                # Handle different line formats
                if len(line.shape) == 3 and line.shape[1] == 1 and line.shape[2] == 4:
                    # Format: [[x1, y1, x2, y2]]
                    x1, y1, x2, y2 = line[0]
                elif len(line.shape) == 2 and line.shape[0] == 1 and line.shape[1] == 4:
                    # Format: [[x1, y1, x2, y2]]
                    x1, y1, x2, y2 = line[0]
                elif len(line.shape) == 1 and len(line) == 4:
                    # Format: [x1, y1, x2, y2]
                    x1, y1, x2, y2 = line
                elif hasattr(line, '__len__') and len(line) == 4:
                    # Format: (x1, y1, x2, y2) or similar
                    x1, y1, x2, y2 = line
                else:
                    # Skip invalid line format
                    logger.debug(f"Skipping line with invalid format: shape={line.shape if hasattr(line, 'shape') else 'no shape'}, len={len(line) if hasattr(line, '__len__') else 'no len'}")
                    continue

                # Convert to integers
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                # Check if line is within image bounds
                if not (0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h):
                    continue

                # Check line length
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                if length < 20:  # Minimum line length
                    continue

                # Check if line is not too steep (avoid noise)
                if length > 0:
                    angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                    if not (angle < 15 or angle > 75):  # Keep horizontal and vertical lines
                        continue

                valid_lines.append(np.array([[x1, y1, x2, y2]]))

            except Exception as e:
                logger.debug(f"Error validating line: {e}")
                continue

        return valid_lines

    def _fuse_and_filter_lines(self, all_lines: List[np.ndarray], image_shape: Tuple[int, int]) -> List[np.ndarray]:
        """Fuse lines from different methods and remove duplicates."""
        if not all_lines:
            return []

        # Group similar lines
        grouped_lines = self._group_similar_lines(all_lines)

        # Select best representative from each group
        final_lines = []
        for group in grouped_lines:
            if len(group) > 0:
                # Select the longest line from the group
                best_line = max(group, key=lambda l: self._calculate_line_length(l))
                final_lines.append(best_line)

        return final_lines

    def _group_similar_lines(self, lines: List[np.ndarray], threshold: float = 20.0) -> List[List[np.ndarray]]:
        """Group similar lines together."""
        if not lines:
            return []

        groups = []
        used = [False] * len(lines)

        for i, line1 in enumerate(lines):
            if used[i]:
                continue

            group = [line1]
            used[i] = True

            for j, line2 in enumerate(lines[i+1:], i+1):
                if used[j]:
                    continue

                if self._lines_similar(line1, line2, threshold):
                    group.append(line2)
                    used[j] = True

            groups.append(group)

        return groups

    def _lines_similar(self, line1: np.ndarray, line2: np.ndarray, threshold: float) -> bool:
        """Check if two lines are similar."""
        try:
            # Extract coordinates for line1
            if len(line1.shape) == 3 and line1.shape[1] == 1 and line1.shape[2] == 4:
                x1, y1, x2, y2 = line1[0]
            elif len(line1.shape) == 2 and line1.shape[0] == 1 and line1.shape[1] == 4:
                x1, y1, x2, y2 = line1[0]
            elif len(line1.shape) == 1 and len(line1) == 4:
                x1, y1, x2, y2 = line1
            else:
                return False

            # Extract coordinates for line2
            if len(line2.shape) == 3 and line2.shape[1] == 1 and line2.shape[2] == 4:
                x3, y3, x4, y4 = line2[0]
            elif len(line2.shape) == 2 and line2.shape[0] == 1 and line2.shape[1] == 4:
                x3, y3, x4, y4 = line2[0]
            elif len(line2.shape) == 1 and len(line2) == 4:
                x3, y3, x4, y4 = line2
            else:
                return False

            # Calculate distance between line centers
            center1 = ((x1 + x2) / 2, (y1 + y2) / 2)
            center2 = ((x3 + x4) / 2, (y3 + y4) / 2)
            distance = np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)

            return distance < threshold
        except Exception:
            return False

    def _calculate_line_length(self, line: np.ndarray) -> float:
        """Calculate line length."""
        try:
            if len(line.shape) == 3 and line.shape[1] == 1 and line.shape[2] == 4:
                x1, y1, x2, y2 = line[0]
            elif len(line.shape) == 2 and line.shape[0] == 1 and line.shape[1] == 4:
                x1, y1, x2, y2 = line[0]
            elif len(line.shape) == 1 and len(line) == 4:
                x1, y1, x2, y2 = line
            else:
                return 0.0
            return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        except Exception:
            return 0.0


@dataclass
class SimplifiedCourtFeatures:
    """Simplified court detection results."""
    confidence_score: float = 0.0
    detection_method: str = "none"
    court_corners: Optional[np.ndarray] = None
    keypoints: Optional[np.ndarray] = None
    homography_matrix: Optional[np.ndarray] = None
    processing_time: float = 0.0

    # Additional court features
    free_throw_lines: Optional[np.ndarray] = None
    center_circle: Optional[np.ndarray] = None
    three_point_arcs: Optional[np.ndarray] = None
    detected_lines: Optional[List[np.ndarray]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'confidence_score': float(self.confidence_score),
            'detection_method': self.detection_method,
            'court_corners': self.court_corners.tolist() if self.court_corners is not None else None,
            'keypoints': self.keypoints.tolist() if self.keypoints is not None else None,
            'has_homography': self.homography_matrix is not None,
            'processing_time': float(self.processing_time),
            'free_throw_lines': self.free_throw_lines.tolist() if self.free_throw_lines is not None else None,
            'center_circle': self.center_circle.tolist() if self.center_circle is not None else None,
            'three_point_arcs': self.three_point_arcs.tolist() if self.three_point_arcs is not None else None,
            'detected_lines_count': len(self.detected_lines) if self.detected_lines else 0,
        }


class CourtHomographyEstimator:
    """Estimates homography for court perspective transformation."""

    def __init__(self):
        self.court_template = BasketballCourtTemplate() if CNN_DETECTION_AVAILABLE else None
        self.min_matches = 4  # Minimum points for homography

    def estimate_homography(self, lines: List[np.ndarray], keypoints: Optional[np.ndarray] = None,
                          image_shape: Tuple[int, int] = None) -> Tuple[Optional[np.ndarray], float]:
        """Estimate homography matrix from detected lines and keypoints."""
        try:
            # Extract court features from lines
            court_features = self._extract_court_features_from_lines(lines, image_shape)

            # Combine with CNN keypoints if available
            if keypoints is not None and len(keypoints) > 0:
                court_features = self._fuse_with_keypoints(court_features, keypoints)

            if len(court_features) < self.min_matches:
                return None, 0.0

            # RANSAC-based homography estimation
            homography, confidence = self._robust_homography_estimation(court_features, image_shape)

            return homography, confidence

        except Exception as e:
            logger.error(f"Homography estimation failed: {e}")
            return None, 0.0

    def _extract_court_features_from_lines(self, lines: List[np.ndarray],
                                         image_shape: Tuple[int, int]) -> List[Tuple[float, float]]:
        """Extract court feature points from detected lines."""
        if not lines or not image_shape:
            return []

        h, w = image_shape[:2]
        feature_points = []

        # Group lines by orientation
        horizontal_lines, vertical_lines = self._group_lines_by_orientation(lines)

        # Find intersections (potential corners)
        for h_line in horizontal_lines[:3]:  # Limit to avoid too many points
            for v_line in vertical_lines[:3]:
                intersection = self._calculate_line_intersection(h_line, v_line)
                if intersection and self._is_valid_intersection(intersection, (h, w)):
                    feature_points.append(intersection)

        # Add line endpoints as features
        for line in lines[:8]:  # Limit number of lines
            try:
                # Handle different line formats
                if len(line.shape) == 3 and line.shape[1] == 1 and line.shape[2] == 4:
                    x1, y1, x2, y2 = line[0]
                elif len(line.shape) == 2 and line.shape[0] == 1 and line.shape[1] == 4:
                    x1, y1, x2, y2 = line[0]
                elif len(line.shape) == 1 and len(line) == 4:
                    x1, y1, x2, y2 = line
                elif hasattr(line, '__len__') and len(line) == 4:
                    x1, y1, x2, y2 = line
                else:
                    continue

                # Add endpoints if they're near image edges (likely court boundaries)
                if self._is_near_edge((x1, y1), (h, w), threshold=50):
                    feature_points.append((float(x1), float(y1)))
                if self._is_near_edge((x2, y2), (h, w), threshold=50):
                    feature_points.append((float(x2), float(y2)))
            except Exception as e:
                logger.debug(f"Error processing line endpoint: {e}")
                continue

        return feature_points

    def _group_lines_by_orientation(self, lines: List[np.ndarray]) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Group lines into horizontal and vertical."""
        horizontal_lines = []
        vertical_lines = []

        for line in lines:
            try:
                # Handle different line formats
                if len(line.shape) == 3 and line.shape[1] == 1 and line.shape[2] == 4:
                    # Format: [[x1, y1, x2, y2]]
                    x1, y1, x2, y2 = line[0]
                elif len(line.shape) == 2 and line.shape[0] == 1 and line.shape[1] == 4:
                    # Format: [[x1, y1, x2, y2]]
                    x1, y1, x2, y2 = line[0]
                elif len(line.shape) == 1 and len(line) == 4:
                    # Format: [x1, y1, x2, y2]
                    x1, y1, x2, y2 = line
                elif hasattr(line, '__len__') and len(line) == 4:
                    # Format: (x1, y1, x2, y2) or similar
                    x1, y1, x2, y2 = line
                else:
                    # Skip invalid line format
                    logger.debug(f"Skipping line with invalid format in grouping: shape={line.shape if hasattr(line, 'shape') else 'no shape'}")
                    continue

                # Calculate angle
                angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

                if angle < 15 or angle > 165:  # Horizontal
                    horizontal_lines.append(line)
                elif 75 < angle < 105:  # Vertical
                    vertical_lines.append(line)

            except Exception as e:
                logger.debug(f"Error grouping line by orientation: {e}")
                continue

        return horizontal_lines, vertical_lines

    def _calculate_line_intersection(self, line1: np.ndarray, line2: np.ndarray) -> Optional[Tuple[float, float]]:
        """Calculate intersection point of two lines."""
        try:
            # Extract coordinates for line1
            if len(line1.shape) == 3 and line1.shape[1] == 1 and line1.shape[2] == 4:
                x1, y1, x2, y2 = line1[0]
            elif len(line1.shape) == 2 and line1.shape[0] == 1 and line1.shape[1] == 4:
                x1, y1, x2, y2 = line1[0]
            elif len(line1.shape) == 1 and len(line1) == 4:
                x1, y1, x2, y2 = line1
            else:
                return None

            # Extract coordinates for line2
            if len(line2.shape) == 3 and line2.shape[1] == 1 and line2.shape[2] == 4:
                x3, y3, x4, y4 = line2[0]
            elif len(line2.shape) == 2 and line2.shape[0] == 1 and line2.shape[1] == 4:
                x3, y3, x4, y4 = line2[0]
            elif len(line2.shape) == 1 and len(line2) == 4:
                x3, y3, x4, y4 = line2
            else:
                return None

            # Calculate intersection using line equations
            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(denom) < 1e-10:  # Lines are parallel
                return None

            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom

            # Calculate intersection point
            ix = x1 + t * (x2 - x1)
            iy = y1 + t * (y2 - y1)

            return (float(ix), float(iy))

        except Exception:
            return None

    def _is_valid_intersection(self, point: Tuple[float, float], image_shape: Tuple[int, int]) -> bool:
        """Check if intersection point is valid."""
        x, y = point
        h, w = image_shape
        return 0 <= x <= w and 0 <= y <= h

    def _is_near_edge(self, point: Tuple[float, float], image_shape: Tuple[int, int], threshold: int = 50) -> bool:
        """Check if point is near image edge."""
        x, y = point
        h, w = image_shape
        return (x < threshold or x > w - threshold or y < threshold or y > h - threshold)

    def _fuse_with_keypoints(self, line_features: List[Tuple[float, float]],
                           keypoints: np.ndarray) -> List[Tuple[float, float]]:
        """Fuse line-based features with CNN keypoints."""
        combined_features = line_features.copy()

        # Add keypoints as features
        if len(keypoints.shape) == 1:
            keypoints = keypoints.reshape(-1, 2)

        for kp in keypoints:
            if len(kp) >= 2:
                combined_features.append((float(kp[0]), float(kp[1])))

        return combined_features

    def _robust_homography_estimation(self, features: List[Tuple[float, float]],
                                    image_shape: Tuple[int, int]) -> Tuple[Optional[np.ndarray], float]:
        """Estimate homography using RANSAC."""
        if len(features) < self.min_matches:
            return None, 0.0

        try:
            # Convert features to numpy array
            src_points = np.array(features, dtype=np.float32)

            # Create corresponding template points (simplified court model)
            dst_points = self._get_template_points(len(features))

            if len(src_points) != len(dst_points):
                # Match the number of points
                min_points = min(len(src_points), len(dst_points))
                src_points = src_points[:min_points]
                dst_points = dst_points[:min_points]

            if len(src_points) >= 4:
                # Estimate homography with RANSAC
                homography, mask = cv2.findHomography(
                    src_points, dst_points,
                    cv2.RANSAC,
                    ransacReprojThreshold=5.0,
                    confidence=0.99
                )

                if homography is not None:
                    # Calculate confidence based on inlier ratio
                    inlier_ratio = np.sum(mask) / len(mask) if mask is not None else 0
                    confidence = float(inlier_ratio)
                    return homography, confidence

            return None, 0.0

        except Exception as e:
            logger.error(f"RANSAC homography estimation failed: {e}")
            return None, 0.0

    def _get_template_points(self, num_points: int) -> np.ndarray:
        """Get template court points for homography estimation."""
        # Simplified basketball court template points (normalized coordinates)
        template_points = np.array([
            [0.0, 0.0],      # Top-left corner
            [1.0, 0.0],      # Top-right corner
            [0.0, 1.0],      # Bottom-left corner
            [1.0, 1.0],      # Bottom-right corner
            [0.5, 0.0],      # Top center
            [0.5, 1.0],      # Bottom center
            [0.0, 0.5],      # Left center
            [1.0, 0.5],      # Right center
            [0.19, 0.2],     # Left free-throw line top
            [0.19, 0.8],     # Left free-throw line bottom
            [0.81, 0.2],     # Right free-throw line top
            [0.81, 0.8],     # Right free-throw line bottom
        ], dtype=np.float32)

        # Scale to image coordinates (assuming 400x300 template)
        template_points[:, 0] *= 400
        template_points[:, 1] *= 300

        # Return the requested number of points
        return template_points[:min(num_points, len(template_points))]


class TemporalConsistencyManager:
    """Manages temporal consistency across video frames."""

    def __init__(self, history_size: int = 5):
        self.detection_history = deque(maxlen=history_size)
        self.confidence_threshold = 0.4
        self.consistency_weight = 0.3

    def update_detection(self, current_detection: SimplifiedCourtFeatures,
                        frame_idx: int) -> SimplifiedCourtFeatures:
        """Update detection with temporal consistency."""
        try:
            # Calculate consistency score with previous detections
            consistency_score = self._calculate_consistency(current_detection)

            # Apply temporal smoothing if consistency is good
            if consistency_score > self.confidence_threshold and len(self.detection_history) > 0:
                smoothed_detection = self._temporal_smoothing(current_detection)
                smoothed_detection.confidence_score = min(1.0,
                    current_detection.confidence_score + consistency_score * self.consistency_weight)
            else:
                smoothed_detection = current_detection

            # Add to history
            self.detection_history.append({
                'frame_idx': frame_idx,
                'detection': smoothed_detection,
                'confidence': smoothed_detection.confidence_score
            })

            return smoothed_detection

        except Exception as e:
            logger.error(f"Temporal consistency update failed: {e}")
            return current_detection

    def _calculate_consistency(self, current_detection: SimplifiedCourtFeatures) -> float:
        """Calculate consistency score with previous detections."""
        if not self.detection_history:
            return 0.0

        try:
            consistency_scores = []

            for hist_entry in self.detection_history:
                prev_detection = hist_entry['detection']

                # Compare corner positions if available
                if (current_detection.court_corners is not None and
                    prev_detection.court_corners is not None):
                    corner_consistency = self._compare_corners(
                        current_detection.court_corners,
                        prev_detection.court_corners
                    )
                    consistency_scores.append(corner_consistency)

                # Compare detection methods
                if current_detection.detection_method == prev_detection.detection_method:
                    consistency_scores.append(0.2)

            return np.mean(consistency_scores) if consistency_scores else 0.0

        except Exception as e:
            logger.error(f"Consistency calculation failed: {e}")
            return 0.0

    def _compare_corners(self, corners1: np.ndarray, corners2: np.ndarray) -> float:
        """Compare corner positions between detections."""
        try:
            if len(corners1) != len(corners2):
                return 0.0

            # Calculate average distance between corresponding corners
            distances = []
            for c1, c2 in zip(corners1, corners2):
                dist = np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
                distances.append(dist)

            avg_distance = np.mean(distances)

            # Convert distance to consistency score (closer = more consistent)
            # Normalize by image diagonal (assuming ~800px diagonal)
            normalized_distance = avg_distance / 800.0
            consistency = max(0.0, 1.0 - normalized_distance)

            return consistency

        except Exception as e:
            logger.error(f"Corner comparison failed: {e}")
            return 0.0

    def _temporal_smoothing(self, current_detection: SimplifiedCourtFeatures) -> SimplifiedCourtFeatures:
        """Apply temporal smoothing to detection results."""
        try:
            if not self.detection_history:
                return current_detection

            smoothed_detection = current_detection

            # Smooth corner positions if available
            if current_detection.court_corners is not None:
                recent_corners = []
                for hist_entry in self.detection_history[-3:]:  # Use last 3 frames
                    if hist_entry['detection'].court_corners is not None:
                        recent_corners.append(hist_entry['detection'].court_corners)

                if recent_corners:
                    # Average corner positions
                    all_corners = np.array([current_detection.court_corners] + recent_corners)
                    smoothed_corners = np.mean(all_corners, axis=0)
                    smoothed_detection.court_corners = smoothed_corners

            return smoothed_detection

        except Exception as e:
            logger.error(f"Temporal smoothing failed: {e}")
            return current_detection


class SimplifiedCourtDetector:
    """
    Enhanced basketball court detector with adaptive multi-method approach.

    This detector combines CNN-based keypoint detection with advanced traditional
    computer vision methods including adaptive parameter tuning, multi-method
    line detection fusion, temporal consistency, and homography-based court mapping.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the enhanced court detector."""
        self.config = config or {}

        # Initialize CNN-based basketball court detector
        self.cnn_detector = None
        if CNN_DETECTION_AVAILABLE and self.config.get('use_cnn_detection', True):
            try:
                # Look for basketball court model weights
                model_path = self.config.get('basketball_model_path', 'models/basketball_court_keypoints.pth')
                tennis_model_path = self.config.get('tennis_model_path', 'models/keypoints_model.pth')

                # Initialize with transfer learning if tennis weights available
                if os.path.exists(tennis_model_path):
                    self.cnn_detector = BasketballCourtKeypointDetector(tennis_weights_path=tennis_model_path)
                    logger.info("Initialized basketball court detector with tennis transfer learning")
                elif os.path.exists(model_path):
                    self.cnn_detector = BasketballCourtKeypointDetector()
                    # Load basketball-specific weights
                    import torch
                    self.cnn_detector.load_state_dict(torch.load(model_path, map_location='cpu'))
                    logger.info("Initialized basketball court detector with trained weights")
                else:
                    # Use pretrained ResNet-50 without specific court weights
                    self.cnn_detector = BasketballCourtKeypointDetector(pretrained=True)
                    logger.info("Initialized basketball court detector with ImageNet pretrained weights")

            except Exception as e:
                logger.warning(f"Could not initialize CNN court detector: {e}. Falling back to traditional methods.")
                self.cnn_detector = None
        else:
            if not CNN_DETECTION_AVAILABLE:
                logger.info("PyTorch not available. Using traditional computer vision methods only.")

        # Initialize enhanced components
        self.parameter_tuner = AdaptiveParameterTuner()
        self.line_detector = AdaptiveLineDetector()
        self.homography_estimator = CourtHomographyEstimator()
        self.temporal_manager = TemporalConsistencyManager()

        # Detection history for adaptive parameter tuning
        self.detection_history = []
        self.frame_counter = 0

    def detect_court(self, frame: np.ndarray, progress_callback=None) -> SimplifiedCourtFeatures:
        """
        Enhanced basketball court detection using adaptive multi-method approach.

        Args:
            frame: Input video frame as numpy array (BGR format)
            progress_callback: Optional callback for progress updates

        Returns:
            SimplifiedCourtFeatures object containing detection results
        """
        start_time = time.perf_counter()
        self.frame_counter += 1

        try:
            if progress_callback:
                progress_callback(5, "Initializing enhanced court detection")

            # Phase 1: Adaptive parameter tuning
            if progress_callback:
                progress_callback(10, "Adapting parameters to image conditions")

            adaptive_params = self.parameter_tuner.adapt_parameters(frame, self.detection_history)

            # Phase 2: Multi-method detection
            cnn_result = None
            if self.cnn_detector is not None:
                if progress_callback:
                    progress_callback(25, "CNN keypoint detection")
                cnn_result = self._detect_with_cnn(frame)
                logger.debug(f"CNN detection confidence: {cnn_result.confidence_score:.3f}")

            # Enhanced line detection
            if progress_callback:
                progress_callback(45, "Enhanced multi-method line detection")

            detected_lines = self.line_detector.detect_lines(frame, adaptive_params)
            logger.debug(f"Detected {len(detected_lines)} lines")

            # Phase 3: Homography estimation and court mapping
            if progress_callback:
                progress_callback(65, "Estimating court homography")

            keypoints = cnn_result.keypoints if cnn_result else None
            homography, homography_confidence = self.homography_estimator.estimate_homography(
                detected_lines, keypoints, frame.shape[:2]
            )

            # Phase 4: Feature extraction and fusion
            if progress_callback:
                progress_callback(80, "Extracting court features")

            court_result = self._create_enhanced_result(
                frame, detected_lines, cnn_result, homography,
                homography_confidence, adaptive_params
            )

            # Phase 5: Temporal consistency
            if progress_callback:
                progress_callback(95, "Applying temporal consistency")

            final_result = self.temporal_manager.update_detection(court_result, self.frame_counter)
            final_result.processing_time = time.perf_counter() - start_time

            # Update detection history
            self.detection_history.append({
                'confidence': final_result.confidence_score,
                'method': final_result.detection_method,
                'frame_idx': self.frame_counter
            })

            # Keep only recent history
            if len(self.detection_history) > 10:
                self.detection_history = self.detection_history[-10:]

            if progress_callback:
                progress_callback(100, "Enhanced court detection complete")

            logger.info(f"Enhanced detection: method={final_result.detection_method}, "
                       f"confidence={final_result.confidence_score:.3f}, "
                       f"lines={len(detected_lines)}, "
                       f"homography={'Yes' if homography is not None else 'No'}")

            return final_result

        except Exception as e:
            logger.error(f"Enhanced court detection failed: {e}")
            result = SimplifiedCourtFeatures(
                confidence_score=0.0,
                detection_method="enhanced_error",
                processing_time=time.perf_counter() - start_time
            )
            return result

    def _create_enhanced_result(self, frame: np.ndarray, detected_lines: List[np.ndarray],
                              cnn_result: Optional[SimplifiedCourtFeatures],
                              homography: Optional[np.ndarray], homography_confidence: float,
                              adaptive_params: Dict[str, Any]) -> SimplifiedCourtFeatures:
        """Create enhanced court detection result from all available information."""
        try:
            # Determine primary detection method and confidence
            if cnn_result and cnn_result.confidence_score > 0.5:
                primary_method = "enhanced_cnn"
                base_confidence = cnn_result.confidence_score
                court_corners = cnn_result.court_corners
                keypoints = cnn_result.keypoints
            elif homography is not None and homography_confidence > 0.3:
                primary_method = "enhanced_homography"
                base_confidence = homography_confidence
                court_corners = self._extract_corners_from_homography(homography, frame.shape)
                keypoints = cnn_result.keypoints if cnn_result else None
            elif len(detected_lines) >= 4:
                primary_method = "enhanced_lines"
                base_confidence = min(0.7, 0.3 + len(detected_lines) * 0.05)
                court_corners = self._extract_corners_from_lines_enhanced(detected_lines, frame.shape)
                keypoints = cnn_result.keypoints if cnn_result else None
            else:
                primary_method = "enhanced_fallback"
                base_confidence = 0.2
                court_corners = None
                keypoints = None

            # Boost confidence based on multiple detection methods agreement
            confidence_boost = 0.0
            if cnn_result and len(detected_lines) > 0:
                confidence_boost += 0.1  # CNN + lines agreement
            if homography is not None and len(detected_lines) > 0:
                confidence_boost += 0.1  # Homography + lines agreement
            if cnn_result and homography is not None:
                confidence_boost += 0.15  # CNN + homography agreement

            final_confidence = min(1.0, base_confidence + confidence_boost)

            # Extract additional court features if homography is available
            free_throw_lines = None
            center_circle = None
            three_point_arcs = None

            if homography is not None:
                free_throw_lines, center_circle, three_point_arcs = self._extract_court_markings(
                    homography, frame.shape
                )

            return SimplifiedCourtFeatures(
                confidence_score=final_confidence,
                detection_method=primary_method,
                court_corners=court_corners,
                keypoints=keypoints,
                homography_matrix=homography,
                detected_lines=detected_lines,
                free_throw_lines=free_throw_lines,
                center_circle=center_circle,
                three_point_arcs=three_point_arcs
            )

        except Exception as e:
            logger.error(f"Error creating enhanced result: {e}")
            return SimplifiedCourtFeatures(
                confidence_score=0.1,
                detection_method="enhanced_error"
            )

    def _extract_corners_from_homography(self, homography: np.ndarray,
                                       frame_shape: Tuple[int, int, int]) -> Optional[np.ndarray]:
        """Extract court corners using homography transformation."""
        try:
            h, w = frame_shape[:2]

            # Template court corners (normalized coordinates)
            template_corners = np.array([
                [0.0, 0.0],      # Top-left
                [1.0, 0.0],      # Top-right
                [0.0, 1.0],      # Bottom-left
                [1.0, 1.0]       # Bottom-right
            ], dtype=np.float32)

            # Scale to template size
            template_corners[:, 0] *= 400
            template_corners[:, 1] *= 300

            # Transform to image coordinates
            corners = cv2.perspectiveTransform(
                template_corners.reshape(-1, 1, 2),
                np.linalg.inv(homography)
            ).reshape(-1, 2)

            # Validate corners are within image bounds
            valid_corners = []
            for corner in corners:
                x, y = corner
                if 0 <= x <= w and 0 <= y <= h:
                    valid_corners.append([x, y])

            return np.array(valid_corners) if len(valid_corners) >= 4 else None

        except Exception as e:
            logger.error(f"Error extracting corners from homography: {e}")
            return None

    def _extract_corners_from_lines_enhanced(self, lines: List[np.ndarray],
                                           frame_shape: Tuple[int, int, int]) -> Optional[np.ndarray]:
        """Enhanced corner extraction from detected lines using intersection analysis."""
        try:
            if not lines or len(lines) < 4:
                return None

            h, w = frame_shape[:2]

            # Group lines by orientation
            horizontal_lines, vertical_lines = self.homography_estimator._group_lines_by_orientation(lines)

            if len(horizontal_lines) < 2 or len(vertical_lines) < 2:
                return None

            # Find intersections
            intersections = []
            for h_line in horizontal_lines[:3]:  # Limit to avoid too many combinations
                for v_line in vertical_lines[:3]:
                    intersection = self.homography_estimator._calculate_line_intersection(h_line, v_line)
                    if intersection and self.homography_estimator._is_valid_intersection(intersection, (h, w)):
                        intersections.append(intersection)

            if len(intersections) < 4:
                return None

            # Sort intersections to form a quadrilateral
            intersections = np.array(intersections)

            # Find corners by position (top-left, top-right, bottom-left, bottom-right)
            corners = self._sort_corners(intersections)

            return corners if len(corners) == 4 else None

        except Exception as e:
            logger.error(f"Error extracting corners from lines: {e}")
            return None

    def _sort_corners(self, points: np.ndarray) -> np.ndarray:
        """Sort points to form a proper quadrilateral."""
        try:
            # Calculate centroid
            centroid = np.mean(points, axis=0)

            # Sort by angle from centroid
            angles = np.arctan2(points[:, 1] - centroid[1], points[:, 0] - centroid[0])
            sorted_indices = np.argsort(angles)

            return points[sorted_indices]

        except Exception:
            return points[:4] if len(points) >= 4 else points

    def _extract_court_markings(self, homography: np.ndarray,
                              frame_shape: Tuple[int, int, int]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """Extract court markings (free throw lines, center circle, 3-point arcs) using homography."""
        try:
            # Template court markings (normalized coordinates)
            free_throw_template = np.array([
                [0.19, 0.2], [0.19, 0.8],  # Left free-throw line
                [0.81, 0.2], [0.81, 0.8]   # Right free-throw line
            ], dtype=np.float32)

            center_circle_template = np.array([
                [0.5, 0.35], [0.5, 0.65]   # Center circle top and bottom
            ], dtype=np.float32)

            three_point_template = np.array([
                [0.1, 0.3], [0.1, 0.7],    # Left 3-point arc
                [0.9, 0.3], [0.9, 0.7]     # Right 3-point arc
            ], dtype=np.float32)

            # Scale templates
            for template in [free_throw_template, center_circle_template, three_point_template]:
                template[:, 0] *= 400
                template[:, 1] *= 300

            # Transform to image coordinates
            inv_homography = np.linalg.inv(homography)

            free_throw_lines = cv2.perspectiveTransform(
                free_throw_template.reshape(-1, 1, 2), inv_homography
            ).reshape(-1, 2)

            center_circle = cv2.perspectiveTransform(
                center_circle_template.reshape(-1, 1, 2), inv_homography
            ).reshape(-1, 2)

            three_point_arcs = cv2.perspectiveTransform(
                three_point_template.reshape(-1, 1, 2), inv_homography
            ).reshape(-1, 2)

            return free_throw_lines, center_circle, three_point_arcs

        except Exception as e:
            logger.error(f"Error extracting court markings: {e}")
            return None, None, None

    def _detect_with_cnn(self, frame: np.ndarray) -> SimplifiedCourtFeatures:
        """Detect court using CNN-based keypoint detection."""
        if not CNN_DETECTION_AVAILABLE or self.cnn_detector is None:
            return SimplifiedCourtFeatures(
                confidence_score=0.0,
                detection_method="cnn_unavailable"
            )

        try:
            # Get CNN prediction
            cnn_result = self.cnn_detector.predict(frame)

            # Convert to simplified format
            return self._convert_cnn_to_simplified_features(cnn_result, frame)

        except Exception as e:
            logger.error(f"CNN detection failed: {e}")
            return SimplifiedCourtFeatures(
                confidence_score=0.0,
                detection_method="cnn_error"
            )

    def _convert_cnn_to_simplified_features(self, cnn_result, frame: np.ndarray) -> SimplifiedCourtFeatures:
        """Convert CNN results to simplified format."""
        try:
            # Extract keypoints (14 points, 28 coordinates)
            keypoints = cnn_result.keypoints.reshape(14, 2)

            # Convert to court corners (first 4 keypoints)
            court_corners = keypoints[:4].astype(int)

            # Calculate homography from template to detected court
            template_corners = np.array([
                [0, 0], [1, 0], [0, 1], [1, 1]
            ], dtype=np.float32)

            # Scale template to frame size for homography calculation
            h, w = frame.shape[:2]
            template_corners[:, 0] *= w
            template_corners[:, 1] *= h

            homography = None
            if len(court_corners) >= 4:
                try:
                    homography, _ = cv2.findHomography(
                        template_corners,
                        court_corners.astype(np.float32),
                        cv2.RANSAC
                    )
                except Exception as e:
                    logger.warning(f"Could not compute homography from CNN keypoints: {e}")

            # Extract other court features from keypoints
            free_throw_lines = keypoints[4:8]  # Free-throw line points
            center_circle = keypoints[8:10]    # Center circle points
            three_point_arcs = keypoints[10:14]  # 3-point arc points

            return SimplifiedCourtFeatures(
                confidence_score=cnn_result.confidence,
                detection_method="cnn_keypoints",
                court_corners=court_corners,
                keypoints=keypoints.flatten(),
                homography_matrix=homography,
                free_throw_lines=free_throw_lines,
                center_circle=center_circle,
                three_point_arcs=three_point_arcs
            )

        except Exception as e:
            logger.error(f"Error converting CNN results: {e}")
            return SimplifiedCourtFeatures(
                confidence_score=0.1,
                detection_method="cnn_conversion_error"
            )

    def _detect_with_traditional_cv(self, frame: np.ndarray) -> SimplifiedCourtFeatures:
        """Enhanced traditional computer vision court detection (fallback method)."""
        try:
            # Use adaptive parameters for fallback detection
            fallback_params = self.parameter_tuner.adapt_parameters(frame)

            # Use enhanced line detection
            detected_lines = self.line_detector.detect_lines(frame, fallback_params)

            if len(detected_lines) < 4:
                return SimplifiedCourtFeatures(
                    confidence_score=0.2,
                    detection_method="enhanced_traditional_insufficient_lines",
                    detected_lines=detected_lines
                )

            # Enhanced corner detection from lines
            corners = self._extract_corners_from_lines_enhanced(detected_lines, frame.shape)

            # Try homography estimation even without CNN
            homography, homography_confidence = self.homography_estimator.estimate_homography(
                detected_lines, None, frame.shape[:2]
            )

            # Calculate confidence based on multiple factors
            base_confidence = 0.3
            if corners is not None and len(corners) >= 4:
                base_confidence += 0.2
            if homography is not None:
                base_confidence += homography_confidence * 0.3
            if len(detected_lines) > 6:
                base_confidence += 0.1

            final_confidence = min(0.8, base_confidence)  # Cap at 0.8 for traditional methods

            # Extract additional features if homography is available
            free_throw_lines = None
            center_circle = None
            three_point_arcs = None

            if homography is not None:
                free_throw_lines, center_circle, three_point_arcs = self._extract_court_markings(
                    homography, frame.shape
                )

            return SimplifiedCourtFeatures(
                confidence_score=final_confidence,
                detection_method="enhanced_traditional",
                court_corners=corners,
                homography_matrix=homography,
                detected_lines=detected_lines,
                free_throw_lines=free_throw_lines,
                center_circle=center_circle,
                three_point_arcs=three_point_arcs
            )

        except Exception as e:
            logger.error(f"Enhanced traditional CV detection failed: {e}")
            return SimplifiedCourtFeatures(
                confidence_score=0.1,
                detection_method="enhanced_traditional_error"
            )



    def draw_court_features(self, frame: np.ndarray, features: SimplifiedCourtFeatures) -> np.ndarray:
        """Enhanced visualization of detected court features."""
        try:
            result_frame = frame.copy()

            # Draw detected lines
            if features.detected_lines:
                for line in features.detected_lines:
                    try:
                        # Handle different line formats
                        if len(line.shape) == 3 and line.shape[1] == 1 and line.shape[2] == 4:
                            x1, y1, x2, y2 = line[0]
                        elif len(line.shape) == 2 and line.shape[0] == 1 and line.shape[1] == 4:
                            x1, y1, x2, y2 = line[0]
                        elif len(line.shape) == 1 and len(line) == 4:
                            x1, y1, x2, y2 = line
                        elif hasattr(line, '__len__') and len(line) == 4:
                            x1, y1, x2, y2 = line
                        else:
                            continue
                        cv2.line(result_frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 2)
                    except Exception as e:
                        logger.debug(f"Error drawing line: {e}")
                        continue

            # Draw court boundary using homography if available
            if features.homography_matrix is not None:
                # Draw court boundary
                court_template = np.array([
                    [0, 0], [400, 0], [400, 300], [0, 300]
                ], dtype=np.float32).reshape(-1, 1, 2)

                court_boundary = cv2.perspectiveTransform(
                    court_template, np.linalg.inv(features.homography_matrix)
                )
                cv2.polylines(result_frame, [court_boundary.astype(int)], True, (0, 255, 0), 3)

                # Draw court markings
                if features.free_throw_lines is not None:
                    for i in range(0, len(features.free_throw_lines), 2):
                        if i + 1 < len(features.free_throw_lines):
                            pt1 = features.free_throw_lines[i].astype(int)
                            pt2 = features.free_throw_lines[i + 1].astype(int)
                            cv2.line(result_frame, tuple(pt1), tuple(pt2), (255, 0, 255), 2)

                if features.center_circle is not None and len(features.center_circle) >= 2:
                    center = features.center_circle[0].astype(int)
                    radius = int(np.linalg.norm(features.center_circle[1] - features.center_circle[0]))
                    cv2.circle(result_frame, tuple(center), radius, (255, 255, 0), 2)

            # Draw court corners
            elif features.court_corners is not None:
                for i, corner in enumerate(features.court_corners):
                    x, y = int(corner[0]), int(corner[1])
                    cv2.circle(result_frame, (x, y), 8, (0, 0, 255), -1)
                    cv2.putText(result_frame, str(i+1), (x+10, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # Draw court boundary from corners
                if len(features.court_corners) >= 4:
                    corners = features.court_corners.astype(int)
                    cv2.polylines(result_frame, [corners], True, (255, 0, 0), 2)

            # Draw CNN keypoints if available
            if features.keypoints is not None:
                keypoints = features.keypoints.reshape(-1, 2)
                for i, (x, y) in enumerate(keypoints):
                    x, y = int(x), int(y)
                    cv2.circle(result_frame, (x, y), 4, (0, 255, 0), -1)
                    cv2.putText(result_frame, f"K{i+1}", (x+5, y-5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

            # Add comprehensive detection info
            info_lines = [
                f"Method: {features.detection_method}",
                f"Confidence: {features.confidence_score:.3f}",
                f"Lines: {len(features.detected_lines) if features.detected_lines else 0}",
                f"Homography: {'Yes' if features.homography_matrix is not None else 'No'}",
                f"Processing: {features.processing_time*1000:.1f}ms"
            ]

            for i, line in enumerate(info_lines):
                y_pos = 25 + i * 20
                cv2.putText(result_frame, line, (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(result_frame, line, (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

            return result_frame

        except Exception as e:
            logger.error(f"Error drawing enhanced court features: {e}")
            return frame