"""
Adaptive Parameter Tuning for Basketball Court Detection - Phase 4

This module implements comprehensive adaptive parameter tuning based on image characteristics,
lighting conditions, and camera angles to optimize court detection performance.

Author: Basketball Analytics Application
Phase: 4 - Adaptive Parameter Tuning
"""

import logging
import numpy as np
import cv2
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)

class CourtType(Enum):
    """Basketball court type classification."""
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    UNKNOWN = "unknown"

class LightingCondition(Enum):
    """Lighting condition classification."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    VERY_POOR = "very_poor"

@dataclass
class ImageCharacteristics:
    """Container for analyzed image characteristics."""
    lighting_level: float  # 0.0 - 1.0
    contrast_level: float  # 0.0 - 1.0
    noise_level: float     # 0.0 - 1.0
    edge_density: float    # 0.0 - 1.0
    brightness: float      # 0.0 - 1.0
    sharpness: float       # 0.0 - 1.0
    court_type: CourtType
    lighting_condition: LightingCondition
    camera_angle: float    # Estimated angle in degrees
    perspective_distortion: float  # 0.0 - 1.0

@dataclass
class AdaptiveParameters:
    """Container for adaptive detection parameters."""
    # Canny edge detection
    canny_low_threshold: int
    canny_high_threshold: int
    canny_aperture_size: int
    
    # Hough transform
    hough_threshold: int
    hough_min_line_length: int
    hough_max_line_gap: int
    hough_rho: float
    hough_theta: float
    
    # Corner detection
    corner_quality_level: float
    corner_min_distance: float
    corner_block_size: int
    corner_k: float
    
    # FAST corner detection
    fast_threshold: int
    fast_nonmax_suppression: bool
    
    # Morphological operations
    morph_kernel_size: int
    morph_iterations: int
    
    # Gaussian blur
    gaussian_kernel_size: int
    gaussian_sigma: float

class AdaptiveParameterTuner:
    """
    Adaptive parameter tuning system for basketball court detection.
    
    This class analyzes image characteristics and automatically adjusts
    detection parameters to optimize performance across different conditions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the adaptive parameter tuner.
        
        Args:
            config: Configuration dictionary with tuning parameters
        """
        self.config = config or {}
        
        # Base parameters (fallback values)
        self.base_params = AdaptiveParameters(
            canny_low_threshold=50,
            canny_high_threshold=150,
            canny_aperture_size=3,
            hough_threshold=80,
            hough_min_line_length=50,
            hough_max_line_gap=10,
            hough_rho=1.0,
            hough_theta=np.pi / 180,
            corner_quality_level=0.01,
            corner_min_distance=10.0,
            corner_block_size=3,
            corner_k=0.04,
            fast_threshold=10,
            fast_nonmax_suppression=True,
            morph_kernel_size=3,
            morph_iterations=1,
            gaussian_kernel_size=5,
            gaussian_sigma=1.0
        )
        
        # Adaptation history for learning
        self.adaptation_history = []
        self.max_history_size = self.config.get('max_history_size', 100)
        
        # Performance tracking
        self.performance_stats = {
            'total_adaptations': 0,
            'successful_adaptations': 0,
            'adaptation_time_ms': []
        }
        
        logger.info("AdaptiveParameterTuner initialized successfully")
    
    def analyze_image_characteristics(self, frame: np.ndarray) -> ImageCharacteristics:
        """
        Comprehensive analysis of image characteristics for parameter adaptation.
        
        Args:
            frame: Input video frame (BGR format)
            
        Returns:
            ImageCharacteristics object with analyzed metrics
        """
        try:
            start_time = time.time()
            
            # Convert to grayscale for analysis
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            
            height, width = gray.shape
            
            # 1. Lighting level analysis (histogram-based)
            lighting_level = self._analyze_lighting_level(gray)
            
            # 2. Contrast level analysis
            contrast_level = self._analyze_contrast_level(gray)
            
            # 3. Noise level analysis
            noise_level = self._analyze_noise_level(gray)
            
            # 4. Edge density analysis
            edge_density = self._analyze_edge_density(gray)
            
            # 5. Brightness analysis
            brightness = self._analyze_brightness(gray)
            
            # 6. Sharpness analysis
            sharpness = self._analyze_sharpness(gray)
            
            # 7. Court type classification
            court_type = self._classify_court_type(frame, gray)
            
            # 8. Lighting condition classification
            lighting_condition = self._classify_lighting_condition(lighting_level, contrast_level)
            
            # 9. Camera angle estimation
            camera_angle = self._estimate_camera_angle(gray)
            
            # 10. Perspective distortion analysis
            perspective_distortion = self._analyze_perspective_distortion(gray)
            
            characteristics = ImageCharacteristics(
                lighting_level=lighting_level,
                contrast_level=contrast_level,
                noise_level=noise_level,
                edge_density=edge_density,
                brightness=brightness,
                sharpness=sharpness,
                court_type=court_type,
                lighting_condition=lighting_condition,
                camera_angle=camera_angle,
                perspective_distortion=perspective_distortion
            )
            
            analysis_time = (time.time() - start_time) * 1000
            logger.debug(f"Image analysis completed in {analysis_time:.2f}ms")
            
            return characteristics
            
        except Exception as e:
            logger.error(f"Error analyzing image characteristics: {str(e)}")
            # Return default characteristics on error
            return ImageCharacteristics(
                lighting_level=0.5, contrast_level=0.5, noise_level=0.5,
                edge_density=0.5, brightness=0.5, sharpness=0.5,
                court_type=CourtType.UNKNOWN,
                lighting_condition=LightingCondition.FAIR,
                camera_angle=0.0, perspective_distortion=0.5
            )
    
    def adapt_parameters(self, characteristics: ImageCharacteristics) -> AdaptiveParameters:
        """
        Adapt detection parameters based on image characteristics.
        
        Args:
            characteristics: Analyzed image characteristics
            
        Returns:
            AdaptiveParameters with optimized values
        """
        try:
            start_time = time.time()
            
            # Start with base parameters
            params = AdaptiveParameters(**self.base_params.__dict__)
            
            # Adapt Canny parameters
            params = self._adapt_canny_parameters(params, characteristics)
            
            # Adapt Hough parameters
            params = self._adapt_hough_parameters(params, characteristics)
            
            # Adapt corner detection parameters
            params = self._adapt_corner_parameters(params, characteristics)
            
            # Adapt morphological parameters
            params = self._adapt_morphological_parameters(params, characteristics)
            
            # Adapt preprocessing parameters
            params = self._adapt_preprocessing_parameters(params, characteristics)
            
            # Store adaptation in history
            self._store_adaptation_history(characteristics, params)
            
            # Update performance stats
            adaptation_time = (time.time() - start_time) * 1000
            self.performance_stats['total_adaptations'] += 1
            self.performance_stats['adaptation_time_ms'].append(adaptation_time)
            
            logger.debug(f"Parameter adaptation completed in {adaptation_time:.2f}ms")
            
            return params
            
        except Exception as e:
            logger.error(f"Error adapting parameters: {str(e)}")
            return self.base_params

    def _analyze_lighting_level(self, gray: np.ndarray) -> float:
        """Analyze lighting level using histogram analysis."""
        try:
            # Calculate histogram
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = hist.flatten() / hist.sum()  # Normalize

            # Calculate weighted average brightness
            brightness_weights = np.arange(256)
            weighted_brightness = np.sum(hist * brightness_weights) / 255.0

            # Analyze distribution characteristics
            # Good lighting has balanced distribution
            # Poor lighting is skewed to dark or bright
            dark_pixels = np.sum(hist[:64])  # Very dark pixels
            bright_pixels = np.sum(hist[192:])  # Very bright pixels
            mid_pixels = np.sum(hist[64:192])  # Mid-tone pixels

            # Lighting quality based on distribution balance
            if mid_pixels > 0.6 and dark_pixels < 0.3 and bright_pixels < 0.3:
                lighting_quality = 0.8 + (mid_pixels - 0.6) * 0.5
            elif dark_pixels > 0.7:  # Too dark
                lighting_quality = 0.3 - (dark_pixels - 0.7) * 0.5
            elif bright_pixels > 0.7:  # Too bright
                lighting_quality = 0.3 - (bright_pixels - 0.7) * 0.5
            else:
                lighting_quality = 0.5

            return np.clip(lighting_quality, 0.0, 1.0)

        except Exception as e:
            logger.error(f"Error analyzing lighting level: {str(e)}")
            return 0.5

    def _analyze_contrast_level(self, gray: np.ndarray) -> float:
        """Analyze contrast level using standard deviation."""
        try:
            # Standard deviation as contrast measure
            std_dev = np.std(gray.astype(np.float32))

            # Normalize to 0-1 range (typical std range is 0-128)
            contrast_level = std_dev / 128.0

            # Also consider local contrast using Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian_var = laplacian.var()

            # Normalize Laplacian variance (typical range 0-10000)
            local_contrast = np.clip(laplacian_var / 10000.0, 0.0, 1.0)

            # Combine global and local contrast
            combined_contrast = 0.7 * contrast_level + 0.3 * local_contrast

            return np.clip(combined_contrast, 0.0, 1.0)

        except Exception as e:
            logger.error(f"Error analyzing contrast level: {str(e)}")
            return 0.5

    def _analyze_noise_level(self, gray: np.ndarray) -> float:
        """Analyze noise level using high-frequency content."""
        try:
            # Apply Gaussian blur and calculate difference
            blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
            noise_map = cv2.absdiff(gray, blurred)

            # Calculate noise level as mean of high-frequency content
            noise_level = np.mean(noise_map) / 255.0

            # Also analyze using gradient magnitude
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

            # High gradient variance indicates noise
            gradient_noise = np.std(gradient_magnitude) / 1000.0

            # Combine noise measures
            combined_noise = 0.6 * noise_level + 0.4 * gradient_noise

            return np.clip(combined_noise, 0.0, 1.0)

        except Exception as e:
            logger.error(f"Error analyzing noise level: {str(e)}")
            return 0.3

    def _analyze_edge_density(self, gray: np.ndarray) -> float:
        """Analyze edge density using Canny edge detection."""
        try:
            # Apply Canny edge detection with moderate parameters
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Calculate edge density
            edge_pixels = np.sum(edges > 0)
            total_pixels = edges.size
            edge_density = edge_pixels / total_pixels

            return np.clip(edge_density, 0.0, 1.0)

        except Exception as e:
            logger.error(f"Error analyzing edge density: {str(e)}")
            return 0.5

    def _analyze_brightness(self, gray: np.ndarray) -> float:
        """Analyze overall brightness level."""
        try:
            # Calculate mean brightness
            brightness = np.mean(gray) / 255.0
            return np.clip(brightness, 0.0, 1.0)

        except Exception as e:
            logger.error(f"Error analyzing brightness: {str(e)}")
            return 0.5

    def _analyze_sharpness(self, gray: np.ndarray) -> float:
        """Analyze image sharpness using Laplacian variance."""
        try:
            # Calculate Laplacian variance as sharpness measure
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = laplacian.var()

            # Normalize to 0-1 range (typical range 0-5000)
            normalized_sharpness = np.clip(sharpness / 5000.0, 0.0, 1.0)

            return normalized_sharpness

        except Exception as e:
            logger.error(f"Error analyzing sharpness: {str(e)}")
            return 0.5

    def _classify_court_type(self, frame: np.ndarray, gray: np.ndarray) -> CourtType:
        """Classify court type (indoor/outdoor) based on visual characteristics."""
        try:
            # Analyze color characteristics for indoor/outdoor classification
            if len(frame.shape) == 3:
                # Convert to HSV for better color analysis
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                # Analyze saturation - outdoor courts typically have more varied colors
                saturation = hsv[:, :, 1]
                avg_saturation = np.mean(saturation) / 255.0

                # Analyze value (brightness) variation
                value = hsv[:, :, 2]
                brightness_variation = np.std(value) / 255.0

                # Outdoor courts typically have:
                # - Higher saturation variation (sky, trees, etc.)
                # - Higher brightness variation (shadows, sunlight)
                if avg_saturation > 0.3 and brightness_variation > 0.2:
                    return CourtType.OUTDOOR
                elif avg_saturation < 0.2 and brightness_variation < 0.15:
                    return CourtType.INDOOR
                else:
                    return CourtType.UNKNOWN
            else:
                # Grayscale analysis - use brightness variation
                brightness_variation = np.std(gray) / 255.0
                if brightness_variation > 0.25:
                    return CourtType.OUTDOOR
                else:
                    return CourtType.INDOOR

        except Exception as e:
            logger.error(f"Error classifying court type: {str(e)}")
            return CourtType.UNKNOWN

    def _classify_lighting_condition(self, lighting_level: float, contrast_level: float) -> LightingCondition:
        """Classify lighting condition based on lighting and contrast levels."""
        try:
            # Combine lighting and contrast for overall assessment
            overall_quality = 0.6 * lighting_level + 0.4 * contrast_level

            if overall_quality >= 0.8:
                return LightingCondition.EXCELLENT
            elif overall_quality >= 0.65:
                return LightingCondition.GOOD
            elif overall_quality >= 0.45:
                return LightingCondition.FAIR
            elif overall_quality >= 0.25:
                return LightingCondition.POOR
            else:
                return LightingCondition.VERY_POOR

        except Exception as e:
            logger.error(f"Error classifying lighting condition: {str(e)}")
            return LightingCondition.FAIR

    def _estimate_camera_angle(self, gray: np.ndarray) -> float:
        """Estimate camera angle based on perspective analysis."""
        try:
            height, width = gray.shape

            # Detect lines to analyze perspective
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50,
                                   minLineLength=width//4, maxLineGap=10)

            if lines is None or len(lines) < 4:
                return 0.0  # Cannot estimate angle

            # Analyze line angles to estimate camera perspective
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                angles.append(abs(angle))

            # Camera angle estimation based on line angle distribution
            # Overhead view: mostly horizontal/vertical lines (0°, 90°)
            # Angled view: more diagonal lines
            horizontal_lines = sum(1 for angle in angles if angle < 15 or angle > 165)
            vertical_lines = sum(1 for angle in angles if 75 < angle < 105)
            diagonal_lines = len(angles) - horizontal_lines - vertical_lines

            if len(angles) > 0:
                diagonal_ratio = diagonal_lines / len(angles)
                # Estimate angle based on diagonal line ratio
                estimated_angle = diagonal_ratio * 45  # Max 45 degrees
            else:
                estimated_angle = 0.0

            return np.clip(estimated_angle, 0.0, 45.0)

        except Exception as e:
            logger.error(f"Error estimating camera angle: {str(e)}")
            return 0.0

    def _analyze_perspective_distortion(self, gray: np.ndarray) -> float:
        """Analyze perspective distortion level."""
        try:
            height, width = gray.shape

            # Analyze aspect ratio distortion
            # Basketball court should have ~1.88 aspect ratio (94/50 feet)
            frame_aspect_ratio = width / height
            ideal_aspect_ratio = 1.88

            aspect_distortion = abs(frame_aspect_ratio - ideal_aspect_ratio) / ideal_aspect_ratio

            # Analyze corner detection to estimate distortion
            corners = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.01,
                                            minDistance=10, blockSize=3)

            if corners is not None and len(corners) >= 4:
                # Analyze corner distribution - uniform distribution indicates less distortion
                corner_points = corners.reshape(-1, 2)

                # Calculate distribution variance
                x_variance = np.var(corner_points[:, 0]) / (width**2)
                y_variance = np.var(corner_points[:, 1]) / (height**2)

                distribution_distortion = abs(x_variance - y_variance)
            else:
                distribution_distortion = 0.5

            # Combine distortion measures
            total_distortion = 0.6 * aspect_distortion + 0.4 * distribution_distortion

            return np.clip(total_distortion, 0.0, 1.0)

        except Exception as e:
            logger.error(f"Error analyzing perspective distortion: {str(e)}")
            return 0.5

    def _adapt_canny_parameters(self, params: AdaptiveParameters,
                               characteristics: ImageCharacteristics) -> AdaptiveParameters:
        """Adapt Canny edge detection parameters based on image characteristics."""
        try:
            # Base thresholds
            base_low = 50
            base_high = 150

            # Adjust based on noise level
            if characteristics.noise_level > 0.7:
                # High noise - increase thresholds to reduce noise sensitivity
                params.canny_low_threshold = int(base_low * 1.5)
                params.canny_high_threshold = int(base_high * 1.5)
            elif characteristics.noise_level < 0.3:
                # Low noise - can use lower thresholds for better edge detection
                params.canny_low_threshold = int(base_low * 0.7)
                params.canny_high_threshold = int(base_high * 0.7)

            # Adjust based on contrast level
            if characteristics.contrast_level < 0.3:
                # Low contrast - lower thresholds to detect weak edges
                params.canny_low_threshold = int(params.canny_low_threshold * 0.6)
                params.canny_high_threshold = int(params.canny_high_threshold * 0.6)
            elif characteristics.contrast_level > 0.8:
                # High contrast - can use higher thresholds
                params.canny_low_threshold = int(params.canny_low_threshold * 1.3)
                params.canny_high_threshold = int(params.canny_high_threshold * 1.3)

            # Adjust aperture size based on sharpness
            if characteristics.sharpness < 0.3:
                params.canny_aperture_size = 5  # Larger aperture for blurry images
            else:
                params.canny_aperture_size = 3  # Standard aperture

            # Ensure valid ranges
            params.canny_low_threshold = np.clip(params.canny_low_threshold, 10, 200)
            params.canny_high_threshold = np.clip(params.canny_high_threshold, 50, 300)
            params.canny_aperture_size = 3 if params.canny_aperture_size not in [3, 5, 7] else params.canny_aperture_size

            return params

        except Exception as e:
            logger.error(f"Error adapting Canny parameters: {str(e)}")
            return params

    def _adapt_hough_parameters(self, params: AdaptiveParameters,
                               characteristics: ImageCharacteristics) -> AdaptiveParameters:
        """Adapt Hough transform parameters based on image characteristics."""
        try:
            # Base parameters
            base_threshold = 80
            base_min_length = 50
            base_max_gap = 10

            # Adjust threshold based on edge density and noise
            if characteristics.edge_density > 0.7:
                # High edge density - increase threshold to reduce false positives
                params.hough_threshold = int(base_threshold * 1.5)
            elif characteristics.edge_density < 0.3:
                # Low edge density - decrease threshold to detect more lines
                params.hough_threshold = int(base_threshold * 0.6)

            # Adjust based on noise level
            if characteristics.noise_level > 0.6:
                # High noise - increase threshold and min line length
                params.hough_threshold = int(params.hough_threshold * 1.3)
                params.hough_min_line_length = int(base_min_length * 1.4)
            elif characteristics.noise_level < 0.3:
                # Low noise - can use more sensitive parameters
                params.hough_threshold = int(params.hough_threshold * 0.8)
                params.hough_min_line_length = int(base_min_length * 0.8)

            # Adjust based on court type
            if characteristics.court_type == CourtType.OUTDOOR:
                # Outdoor courts may have broken lines - increase max gap
                params.hough_max_line_gap = int(base_max_gap * 2)
            else:
                params.hough_max_line_gap = base_max_gap

            # Adjust based on camera angle
            if characteristics.camera_angle > 30:
                # High angle - lines may be shorter due to perspective
                params.hough_min_line_length = int(params.hough_min_line_length * 0.7)

            # Ensure valid ranges
            params.hough_threshold = np.clip(params.hough_threshold, 30, 200)
            params.hough_min_line_length = np.clip(params.hough_min_line_length, 20, 200)
            params.hough_max_line_gap = np.clip(params.hough_max_line_gap, 5, 50)

            return params

        except Exception as e:
            logger.error(f"Error adapting Hough parameters: {str(e)}")
            return params

    def _adapt_corner_parameters(self, params: AdaptiveParameters,
                                characteristics: ImageCharacteristics) -> AdaptiveParameters:
        """Adapt corner detection parameters based on image characteristics."""
        try:
            # Adjust quality level based on noise and sharpness
            if characteristics.noise_level > 0.6:
                # High noise - increase quality threshold
                params.corner_quality_level = 0.02
            elif characteristics.sharpness > 0.7:
                # Sharp image - can use lower quality threshold
                params.corner_quality_level = 0.005
            else:
                params.corner_quality_level = 0.01

            # Adjust minimum distance based on image resolution and perspective
            base_distance = 10.0
            if characteristics.perspective_distortion > 0.6:
                # High distortion - corners may be closer together
                params.corner_min_distance = base_distance * 0.7
            else:
                params.corner_min_distance = base_distance

            # Adjust FAST threshold based on lighting and contrast
            if characteristics.lighting_condition in [LightingCondition.POOR, LightingCondition.VERY_POOR]:
                # Poor lighting - lower threshold for better detection
                params.fast_threshold = 5
            elif characteristics.contrast_level > 0.8:
                # High contrast - can use higher threshold
                params.fast_threshold = 15
            else:
                params.fast_threshold = 10

            # Ensure valid ranges
            params.corner_quality_level = np.clip(params.corner_quality_level, 0.001, 0.1)
            params.corner_min_distance = np.clip(params.corner_min_distance, 5.0, 50.0)
            params.fast_threshold = np.clip(params.fast_threshold, 1, 50)

            return params

        except Exception as e:
            logger.error(f"Error adapting corner parameters: {str(e)}")
            return params

    def _adapt_morphological_parameters(self, params: AdaptiveParameters,
                                       characteristics: ImageCharacteristics) -> AdaptiveParameters:
        """Adapt morphological operation parameters."""
        try:
            # Adjust kernel size based on noise level
            if characteristics.noise_level > 0.7:
                # High noise - larger kernel for better noise reduction
                params.morph_kernel_size = 5
                params.morph_iterations = 2
            elif characteristics.noise_level < 0.3:
                # Low noise - smaller kernel to preserve details
                params.morph_kernel_size = 3
                params.morph_iterations = 1
            else:
                params.morph_kernel_size = 3
                params.morph_iterations = 1

            # Ensure odd kernel sizes
            if params.morph_kernel_size % 2 == 0:
                params.morph_kernel_size += 1

            params.morph_kernel_size = np.clip(params.morph_kernel_size, 3, 7)
            params.morph_iterations = np.clip(params.morph_iterations, 1, 3)

            return params

        except Exception as e:
            logger.error(f"Error adapting morphological parameters: {str(e)}")
            return params

    def _adapt_preprocessing_parameters(self, params: AdaptiveParameters,
                                       characteristics: ImageCharacteristics) -> AdaptiveParameters:
        """Adapt preprocessing parameters (Gaussian blur, etc.)."""
        try:
            # Adjust Gaussian blur based on noise and sharpness
            if characteristics.noise_level > 0.6:
                # High noise - more blur to reduce noise
                params.gaussian_kernel_size = 7
                params.gaussian_sigma = 1.5
            elif characteristics.sharpness < 0.3:
                # Already blurry - minimal additional blur
                params.gaussian_kernel_size = 3
                params.gaussian_sigma = 0.5
            else:
                # Standard blur
                params.gaussian_kernel_size = 5
                params.gaussian_sigma = 1.0

            # Ensure odd kernel sizes
            if params.gaussian_kernel_size % 2 == 0:
                params.gaussian_kernel_size += 1

            params.gaussian_kernel_size = np.clip(params.gaussian_kernel_size, 3, 9)
            params.gaussian_sigma = np.clip(params.gaussian_sigma, 0.1, 3.0)

            return params

        except Exception as e:
            logger.error(f"Error adapting preprocessing parameters: {str(e)}")
            return params

    def _store_adaptation_history(self, characteristics: ImageCharacteristics,
                                 params: AdaptiveParameters) -> None:
        """Store adaptation history for learning and analysis."""
        try:
            history_entry = {
                'timestamp': time.time(),
                'characteristics': characteristics,
                'parameters': params
            }

            self.adaptation_history.append(history_entry)

            # Maintain history size limit
            if len(self.adaptation_history) > self.max_history_size:
                self.adaptation_history.pop(0)

        except Exception as e:
            logger.error(f"Error storing adaptation history: {str(e)}")

    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """Get statistics about parameter adaptations."""
        try:
            stats = self.performance_stats.copy()

            if stats['adaptation_time_ms']:
                stats['avg_adaptation_time_ms'] = np.mean(stats['adaptation_time_ms'])
                stats['max_adaptation_time_ms'] = np.max(stats['adaptation_time_ms'])
                stats['min_adaptation_time_ms'] = np.min(stats['adaptation_time_ms'])

            stats['history_size'] = len(self.adaptation_history)

            if stats['total_adaptations'] > 0:
                stats['success_rate'] = stats['successful_adaptations'] / stats['total_adaptations']
            else:
                stats['success_rate'] = 0.0

            return stats

        except Exception as e:
            logger.error(f"Error getting adaptation statistics: {str(e)}")
            return {'error': str(e)}

    def reset_statistics(self) -> None:
        """Reset adaptation statistics."""
        try:
            self.performance_stats = {
                'total_adaptations': 0,
                'successful_adaptations': 0,
                'adaptation_time_ms': []
            }
            logger.info("Adaptation statistics reset")

        except Exception as e:
            logger.error(f"Error resetting statistics: {str(e)}")

    def export_adaptation_history(self, filepath: str) -> bool:
        """Export adaptation history to file for analysis."""
        try:
            import json

            # Convert history to serializable format
            serializable_history = []
            for entry in self.adaptation_history:
                serializable_entry = {
                    'timestamp': entry['timestamp'],
                    'characteristics': {
                        'lighting_level': entry['characteristics'].lighting_level,
                        'contrast_level': entry['characteristics'].contrast_level,
                        'noise_level': entry['characteristics'].noise_level,
                        'edge_density': entry['characteristics'].edge_density,
                        'brightness': entry['characteristics'].brightness,
                        'sharpness': entry['characteristics'].sharpness,
                        'court_type': entry['characteristics'].court_type.value,
                        'lighting_condition': entry['characteristics'].lighting_condition.value,
                        'camera_angle': entry['characteristics'].camera_angle,
                        'perspective_distortion': entry['characteristics'].perspective_distortion
                    },
                    'parameters': entry['parameters'].__dict__
                }
                serializable_history.append(serializable_entry)

            with open(filepath, 'w') as f:
                json.dump({
                    'adaptation_history': serializable_history,
                    'statistics': self.get_adaptation_statistics()
                }, f, indent=2)

            logger.info(f"Adaptation history exported to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error exporting adaptation history: {str(e)}")
            return False
