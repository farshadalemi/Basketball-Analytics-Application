"""
Accuracy measurement tools for basketball court detection validation.

This module provides comprehensive accuracy metrics including IoU calculations,
corner detection accuracy, geometric validation, and statistical analysis.
"""

import numpy as np
import cv2
import logging
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import time

try:
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class AccuracyResult:
    """Container for accuracy measurement results."""
    iou_score: float
    corner_accuracy: float
    aspect_ratio_error: float
    geometric_validity: bool
    confidence_score: float
    processing_time_ms: float
    method_name: str
    additional_metrics: Dict[str, float]

class AccuracyMetrics:
    """
    Comprehensive accuracy measurement tools for court detection validation.
    
    This class provides various metrics to evaluate the performance of
    basketball court detection algorithms against ground truth data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize accuracy metrics calculator.
        
        Args:
            config: Configuration dictionary with metric parameters
        """
        self.config = config or {}
        
        # Accuracy thresholds
        self.corner_distance_threshold = self.config.get('corner_distance_threshold', 20.0)
        self.aspect_ratio_tolerance = self.config.get('aspect_ratio_tolerance', 0.15)
        self.iou_threshold = self.config.get('iou_threshold', 0.5)
        
        # Basketball court specifications
        self.ideal_aspect_ratio = 94.0 / 50.0  # NBA court dimensions
        
        # Statistics tracking
        self.measurement_history = []
        
        logger.info("AccuracyMetrics initialized successfully")
    
    def calculate_comprehensive_accuracy(self, predicted_corners: List[Tuple[float, float]], 
                                       ground_truth_corners: List[Tuple[float, float]],
                                       confidence_score: float = 1.0,
                                       method_name: str = "unknown") -> AccuracyResult:
        """
        Calculate comprehensive accuracy metrics for court detection.
        
        Args:
            predicted_corners: List of predicted corner points
            ground_truth_corners: List of ground truth corner points
            confidence_score: Detection confidence score
            method_name: Name of the detection method
            
        Returns:
            AccuracyResult with comprehensive metrics
        """
        try:
            start_time = time.perf_counter()
            
            # Calculate IoU score
            iou_score = self.calculate_iou(predicted_corners, ground_truth_corners)
            
            # Calculate corner accuracy
            corner_accuracy = self.calculate_corner_accuracy(predicted_corners, ground_truth_corners)
            
            # Calculate aspect ratio error
            aspect_ratio_error = self.calculate_aspect_ratio_error(predicted_corners, ground_truth_corners)
            
            # Validate geometric properties
            geometric_validity = self.validate_geometric_properties(predicted_corners)
            
            # Calculate additional metrics
            additional_metrics = self._calculate_additional_metrics(
                predicted_corners, ground_truth_corners
            )
            
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            
            result = AccuracyResult(
                iou_score=iou_score,
                corner_accuracy=corner_accuracy,
                aspect_ratio_error=aspect_ratio_error,
                geometric_validity=geometric_validity,
                confidence_score=confidence_score,
                processing_time_ms=processing_time_ms,
                method_name=method_name,
                additional_metrics=additional_metrics
            )
            
            # Store in history
            self.measurement_history.append(result)
            
            logger.debug(f"Accuracy calculated for {method_name}: IoU={iou_score:.3f}, "
                        f"Corner={corner_accuracy:.3f}, AspectError={aspect_ratio_error:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive accuracy: {str(e)}")
            return AccuracyResult(
                iou_score=0.0, corner_accuracy=0.0, aspect_ratio_error=1.0,
                geometric_validity=False, confidence_score=confidence_score,
                processing_time_ms=0.0, method_name=method_name,
                additional_metrics={}
            )
    
    def calculate_iou(self, predicted_corners: List[Tuple[float, float]], 
                     ground_truth_corners: List[Tuple[float, float]]) -> float:
        """
        Calculate Intersection over Union (IoU) for court detection.
        
        Args:
            predicted_corners: List of predicted corner points
            ground_truth_corners: List of ground truth corner points
            
        Returns:
            IoU score (0-1)
        """
        try:
            if len(predicted_corners) < 4 or len(ground_truth_corners) < 4:
                return 0.0
            
            if SHAPELY_AVAILABLE:
                # Use Shapely for accurate polygon operations
                pred_polygon = Polygon(predicted_corners[:4])
                gt_polygon = Polygon(ground_truth_corners[:4])
                
                if not pred_polygon.is_valid or not gt_polygon.is_valid:
                    return 0.0
                
                intersection = pred_polygon.intersection(gt_polygon).area
                union = pred_polygon.union(gt_polygon).area
                
                if union == 0:
                    return 0.0
                
                return intersection / union
            else:
                # Fallback to OpenCV-based calculation
                return self._calculate_iou_opencv(predicted_corners, ground_truth_corners)
                
        except Exception as e:
            logger.error(f"Error calculating IoU: {str(e)}")
            return 0.0
    
    def _calculate_iou_opencv(self, predicted_corners: List[Tuple[float, float]], 
                             ground_truth_corners: List[Tuple[float, float]]) -> float:
        """Fallback IoU calculation using OpenCV."""
        try:
            # Create binary masks for both polygons
            # Determine bounding box for both polygons
            all_points = predicted_corners + ground_truth_corners
            x_coords = [p[0] for p in all_points]
            y_coords = [p[1] for p in all_points]
            
            min_x, max_x = int(min(x_coords)), int(max(x_coords))
            min_y, max_y = int(min(y_coords)), int(max(y_coords))
            
            width = max_x - min_x + 1
            height = max_y - min_y + 1
            
            # Create masks
            pred_mask = np.zeros((height, width), dtype=np.uint8)
            gt_mask = np.zeros((height, width), dtype=np.uint8)
            
            # Adjust coordinates to mask space
            pred_points = np.array([(int(p[0] - min_x), int(p[1] - min_y)) for p in predicted_corners[:4]])
            gt_points = np.array([(int(p[0] - min_x), int(p[1] - min_y)) for p in ground_truth_corners[:4]])
            
            # Fill polygons
            cv2.fillPoly(pred_mask, [pred_points], 255)
            cv2.fillPoly(gt_mask, [gt_points], 255)
            
            # Calculate intersection and union
            intersection = np.logical_and(pred_mask, gt_mask).sum()
            union = np.logical_or(pred_mask, gt_mask).sum()
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"Error in OpenCV IoU calculation: {str(e)}")
            return 0.0
    
    def calculate_corner_accuracy(self, predicted_corners: List[Tuple[float, float]], 
                                 ground_truth_corners: List[Tuple[float, float]],
                                 threshold: Optional[float] = None) -> float:
        """
        Calculate corner detection accuracy within pixel threshold.
        
        Args:
            predicted_corners: List of predicted corner points
            ground_truth_corners: List of ground truth corner points
            threshold: Maximum distance in pixels for correct detection
            
        Returns:
            Accuracy score (0-1)
        """
        try:
            if threshold is None:
                threshold = self.corner_distance_threshold
            
            if len(predicted_corners) < 4 or len(ground_truth_corners) < 4:
                return 0.0
            
            # Use Hungarian algorithm for optimal corner matching
            correct_corners = 0
            used_predicted = set()
            
            for gt_corner in ground_truth_corners[:4]:
                min_distance = float('inf')
                best_pred_idx = -1
                
                for i, pred_corner in enumerate(predicted_corners):
                    if i in used_predicted:
                        continue
                        
                    distance = np.sqrt(
                        (pred_corner[0] - gt_corner[0])**2 +
                        (pred_corner[1] - gt_corner[1])**2
                    )
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_pred_idx = i
                
                if best_pred_idx != -1 and min_distance <= threshold:
                    correct_corners += 1
                    used_predicted.add(best_pred_idx)
            
            return correct_corners / 4.0
            
        except Exception as e:
            logger.error(f"Error calculating corner accuracy: {str(e)}")
            return 0.0
    
    def calculate_aspect_ratio_error(self, predicted_corners: List[Tuple[float, float]], 
                                   ground_truth_corners: List[Tuple[float, float]]) -> float:
        """
        Calculate aspect ratio error between predicted and ground truth.
        
        Args:
            predicted_corners: List of predicted corner points
            ground_truth_corners: List of ground truth corner points
            
        Returns:
            Relative error in aspect ratio
        """
        try:
            def get_aspect_ratio(corners):
                if len(corners) < 4:
                    return 0
                x_coords = [c[0] for c in corners[:4]]
                y_coords = [c[1] for c in corners[:4]]
                width = max(x_coords) - min(x_coords)
                height = max(y_coords) - min(y_coords)
                return width / height if height > 0 else 0
            
            pred_ratio = get_aspect_ratio(predicted_corners)
            gt_ratio = get_aspect_ratio(ground_truth_corners)
            
            if gt_ratio == 0:
                return 1.0  # Maximum error
            
            return abs(pred_ratio - gt_ratio) / gt_ratio
            
        except Exception as e:
            logger.error(f"Error calculating aspect ratio error: {str(e)}")
            return 1.0
    
    def validate_geometric_properties(self, corners: List[Tuple[float, float]]) -> bool:
        """
        Validate geometric properties of detected court corners.
        
        Args:
            corners: List of corner points
            
        Returns:
            True if geometry is valid, False otherwise
        """
        try:
            if len(corners) < 4:
                return False
            
            # Check if corners form a convex quadrilateral
            if not self._is_convex_quadrilateral(corners[:4]):
                return False
            
            # Check aspect ratio is reasonable for basketball court
            aspect_ratio = self._get_aspect_ratio(corners[:4])
            if abs(aspect_ratio - self.ideal_aspect_ratio) / self.ideal_aspect_ratio > self.aspect_ratio_tolerance:
                return False
            
            # Check minimum area (court should be reasonably sized)
            area = self._calculate_polygon_area(corners[:4])
            if area < 1000:  # Minimum area threshold
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating geometric properties: {str(e)}")
            return False

    def _calculate_additional_metrics(self, predicted_corners: List[Tuple[float, float]],
                                    ground_truth_corners: List[Tuple[float, float]]) -> Dict[str, float]:
        """Calculate additional accuracy metrics."""
        try:
            metrics = {}

            # Centroid distance
            if len(predicted_corners) >= 4 and len(ground_truth_corners) >= 4:
                pred_centroid = self._calculate_centroid(predicted_corners[:4])
                gt_centroid = self._calculate_centroid(ground_truth_corners[:4])

                centroid_distance = np.sqrt(
                    (pred_centroid[0] - gt_centroid[0])**2 +
                    (pred_centroid[1] - gt_centroid[1])**2
                )
                metrics['centroid_distance'] = centroid_distance

            # Area ratio
            pred_area = self._calculate_polygon_area(predicted_corners[:4])
            gt_area = self._calculate_polygon_area(ground_truth_corners[:4])

            if gt_area > 0:
                metrics['area_ratio'] = pred_area / gt_area
                metrics['area_error'] = abs(pred_area - gt_area) / gt_area

            # Perimeter ratio
            pred_perimeter = self._calculate_perimeter(predicted_corners[:4])
            gt_perimeter = self._calculate_perimeter(ground_truth_corners[:4])

            if gt_perimeter > 0:
                metrics['perimeter_ratio'] = pred_perimeter / gt_perimeter

            return metrics

        except Exception as e:
            logger.error(f"Error calculating additional metrics: {str(e)}")
            return {}

    def _is_convex_quadrilateral(self, corners: List[Tuple[float, float]]) -> bool:
        """Check if corners form a convex quadrilateral."""
        try:
            if len(corners) != 4:
                return False

            # Calculate cross products to check convexity
            def cross_product(o, a, b):
                return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

            # Check if all cross products have the same sign
            signs = []
            for i in range(4):
                o = corners[i]
                a = corners[(i + 1) % 4]
                b = corners[(i + 2) % 4]
                cp = cross_product(o, a, b)
                signs.append(1 if cp > 0 else -1 if cp < 0 else 0)

            # All signs should be the same (all positive or all negative)
            return len(set(signs)) <= 1

        except Exception as e:
            logger.error(f"Error checking convex quadrilateral: {str(e)}")
            return False

    def _get_aspect_ratio(self, corners: List[Tuple[float, float]]) -> float:
        """Calculate aspect ratio of corners."""
        try:
            x_coords = [c[0] for c in corners]
            y_coords = [c[1] for c in corners]
            width = max(x_coords) - min(x_coords)
            height = max(y_coords) - min(y_coords)
            return width / height if height > 0 else 0
        except Exception as e:
            logger.error(f"Error calculating aspect ratio: {str(e)}")
            return 0

    def _calculate_polygon_area(self, corners: List[Tuple[float, float]]) -> float:
        """Calculate polygon area using shoelace formula."""
        try:
            if len(corners) < 3:
                return 0

            area = 0
            n = len(corners)
            for i in range(n):
                j = (i + 1) % n
                area += corners[i][0] * corners[j][1]
                area -= corners[j][0] * corners[i][1]

            return abs(area) / 2.0

        except Exception as e:
            logger.error(f"Error calculating polygon area: {str(e)}")
            return 0

    def _calculate_centroid(self, corners: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Calculate centroid of corners."""
        try:
            x_sum = sum(c[0] for c in corners)
            y_sum = sum(c[1] for c in corners)
            n = len(corners)
            return (x_sum / n, y_sum / n)
        except Exception as e:
            logger.error(f"Error calculating centroid: {str(e)}")
            return (0, 0)

    def _calculate_perimeter(self, corners: List[Tuple[float, float]]) -> float:
        """Calculate perimeter of polygon."""
        try:
            if len(corners) < 2:
                return 0

            perimeter = 0
            n = len(corners)
            for i in range(n):
                j = (i + 1) % n
                distance = np.sqrt(
                    (corners[j][0] - corners[i][0])**2 +
                    (corners[j][1] - corners[i][1])**2
                )
                perimeter += distance

            return perimeter

        except Exception as e:
            logger.error(f"Error calculating perimeter: {str(e)}")
            return 0

    def get_accuracy_statistics(self) -> Dict[str, Any]:
        """Get comprehensive accuracy statistics from measurement history."""
        try:
            if not self.measurement_history:
                return {'error': 'No measurements available'}

            # Calculate statistics for each metric
            iou_scores = [r.iou_score for r in self.measurement_history]
            corner_accuracies = [r.corner_accuracy for r in self.measurement_history]
            aspect_errors = [r.aspect_ratio_error for r in self.measurement_history]
            processing_times = [r.processing_time_ms for r in self.measurement_history]

            stats = {
                'total_measurements': len(self.measurement_history),
                'iou_statistics': {
                    'mean': np.mean(iou_scores),
                    'std': np.std(iou_scores),
                    'min': np.min(iou_scores),
                    'max': np.max(iou_scores),
                    'median': np.median(iou_scores)
                },
                'corner_accuracy_statistics': {
                    'mean': np.mean(corner_accuracies),
                    'std': np.std(corner_accuracies),
                    'min': np.min(corner_accuracies),
                    'max': np.max(corner_accuracies),
                    'median': np.median(corner_accuracies)
                },
                'aspect_error_statistics': {
                    'mean': np.mean(aspect_errors),
                    'std': np.std(aspect_errors),
                    'min': np.min(aspect_errors),
                    'max': np.max(aspect_errors),
                    'median': np.median(aspect_errors)
                },
                'processing_time_statistics': {
                    'mean_ms': np.mean(processing_times),
                    'std_ms': np.std(processing_times),
                    'min_ms': np.min(processing_times),
                    'max_ms': np.max(processing_times),
                    'median_ms': np.median(processing_times)
                },
                'geometric_validity_rate': sum(1 for r in self.measurement_history if r.geometric_validity) / len(self.measurement_history)
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting accuracy statistics: {str(e)}")
            return {'error': str(e)}

    def reset_history(self):
        """Reset measurement history."""
        self.measurement_history = []
        logger.info("Accuracy measurement history reset")
