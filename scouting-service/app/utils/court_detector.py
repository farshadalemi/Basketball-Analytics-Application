"""Basketball court detection and mapping."""
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from app.core.logging import logger


class CourtDetector:
    """Basketball court detection and mapping."""
    
    def __init__(self):
        """Initialize the court detector."""
        # Standard basketball court dimensions (in feet)
        self.court_length = 94.0
        self.court_width = 50.0
        self.three_point_distance = 23.75  # NBA 3-point distance
        
        # Court features
        self.court_features = {
            'center_circle': {'radius': 6.0},
            'free_throw_line': {'distance_from_baseline': 19.0},
            'free_throw_circle': {'radius': 6.0},
            'three_point_line': {'distance': self.three_point_distance},
            'key': {'width': 16.0, 'length': 19.0}
        }
    
    def detect_court(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Detect basketball court in a frame.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Court detection with court lines and features
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply Canny edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Dilate edges to connect broken lines
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=1)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLinesP(
                dilated,
                rho=1,
                theta=np.pi/180,
                threshold=100,
                minLineLength=100,
                maxLineGap=50
            )
            
            if lines is None:
                logger.warning("No court lines detected")
                return self._generate_default_court(frame.shape[1], frame.shape[0])
            
            # Separate horizontal and vertical lines
            horizontal_lines = []
            vertical_lines = []
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate line angle
                angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
                
                # Classify as horizontal or vertical
                if angle < 30 or angle > 150:
                    horizontal_lines.append(line[0])
                elif angle > 60 and angle < 120:
                    vertical_lines.append(line[0])
            
            # Find court boundaries
            court_boundaries = self._find_court_boundaries(horizontal_lines, vertical_lines, frame.shape)
            
            # Detect court features
            court_features = self._detect_court_features(frame, court_boundaries)
            
            # Create court mapping
            court_mapping = self._create_court_mapping(court_boundaries, court_features)
            
            return {
                'boundaries': court_boundaries,
                'features': court_features,
                'mapping': court_mapping
            }
        except Exception as e:
            logger.error(f"Error in court detection: {e}")
            return self._generate_default_court(frame.shape[1], frame.shape[0])
    
    def _find_court_boundaries(self, horizontal_lines: List[np.ndarray], vertical_lines: List[np.ndarray], frame_shape: Tuple[int, int, int]) -> Dict[str, Any]:
        """
        Find court boundaries from detected lines.
        
        Args:
            horizontal_lines: List of horizontal lines
            vertical_lines: List of vertical lines
            frame_shape: Frame dimensions (height, width, channels)
            
        Returns:
            Court boundaries
        """
        height, width = frame_shape[0], frame_shape[1]
        
        # Default boundaries
        top = 0
        bottom = height
        left = 0
        right = width
        
        # Find top and bottom boundaries from horizontal lines
        if horizontal_lines:
            y_coords = [line[1] for line in horizontal_lines] + [line[3] for line in horizontal_lines]
            y_coords.sort()
            
            # Top boundary is the first significant horizontal line
            for y in y_coords:
                if y > height * 0.1:  # Skip lines too close to the top
                    top = y
                    break
            
            # Bottom boundary is the last significant horizontal line
            for y in reversed(y_coords):
                if y < height * 0.9:  # Skip lines too close to the bottom
                    bottom = y
                    break
        
        # Find left and right boundaries from vertical lines
        if vertical_lines:
            x_coords = [line[0] for line in vertical_lines] + [line[2] for line in vertical_lines]
            x_coords.sort()
            
            # Left boundary is the first significant vertical line
            for x in x_coords:
                if x > width * 0.1:  # Skip lines too close to the left
                    left = x
                    break
            
            # Right boundary is the last significant vertical line
            for x in reversed(x_coords):
                if x < width * 0.9:  # Skip lines too close to the right
                    right = x
                    break
        
        return {
            'top': top,
            'bottom': bottom,
            'left': left,
            'right': right,
            'width': right - left,
            'height': bottom - top
        }
    
    def _detect_court_features(self, frame: np.ndarray, boundaries: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect court features like circles, free throw lines, etc.
        
        Args:
            frame: Video frame
            boundaries: Court boundaries
            
        Returns:
            Detected court features
        """
        # For now, return estimated positions based on court boundaries
        court_width = boundaries['right'] - boundaries['left']
        court_height = boundaries['bottom'] - boundaries['top']
        
        # Center of the court
        center_x = boundaries['left'] + court_width // 2
        center_y = boundaries['top'] + court_height // 2
        
        # Estimate basket positions
        top_basket_y = boundaries['top'] + court_height * 0.1
        bottom_basket_y = boundaries['bottom'] - court_height * 0.1
        
        return {
            'center': (center_x, center_y),
            'baskets': [
                {'position': (center_x, int(top_basket_y))},
                {'position': (center_x, int(bottom_basket_y))}
            ]
        }
    
    def _create_court_mapping(self, boundaries: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create mapping between pixel coordinates and court coordinates.
        
        Args:
            boundaries: Court boundaries
            features: Court features
            
        Returns:
            Court mapping
        """
        # Create transformation matrix
        court_width = boundaries['right'] - boundaries['left']
        court_height = boundaries['bottom'] - boundaries['top']
        
        # Scale factors
        scale_x = self.court_width / court_width
        scale_y = self.court_length / court_height
        
        # Origin in pixel coordinates (bottom left corner of court)
        origin_x = boundaries['left']
        origin_y = boundaries['bottom']
        
        return {
            'scale_x': scale_x,
            'scale_y': scale_y,
            'origin_x': origin_x,
            'origin_y': origin_y
        }
    
    def pixel_to_court(self, pixel_coords: Tuple[int, int], court_mapping: Dict[str, Any]) -> Tuple[float, float]:
        """
        Convert pixel coordinates to court coordinates.
        
        Args:
            pixel_coords: Pixel coordinates (x, y)
            court_mapping: Court mapping
            
        Returns:
            Court coordinates (x, y) in feet
        """
        pixel_x, pixel_y = pixel_coords
        
        # Apply transformation
        court_x = (pixel_x - court_mapping['origin_x']) * court_mapping['scale_x']
        court_y = (court_mapping['origin_y'] - pixel_y) * court_mapping['scale_y']
        
        return (court_x, court_y)
    
    def court_to_pixel(self, court_coords: Tuple[float, float], court_mapping: Dict[str, Any]) -> Tuple[int, int]:
        """
        Convert court coordinates to pixel coordinates.
        
        Args:
            court_coords: Court coordinates (x, y) in feet
            court_mapping: Court mapping
            
        Returns:
            Pixel coordinates (x, y)
        """
        court_x, court_y = court_coords
        
        # Apply inverse transformation
        pixel_x = int(court_x / court_mapping['scale_x'] + court_mapping['origin_x'])
        pixel_y = int(court_mapping['origin_y'] - court_y / court_mapping['scale_y'])
        
        return (pixel_x, pixel_y)
    
    def _generate_default_court(self, width: int, height: int) -> Dict[str, Any]:
        """
        Generate default court when detection fails.
        
        Args:
            width: Frame width
            height: Frame height
            
        Returns:
            Default court information
        """
        # Default boundaries
        boundaries = {
            'top': int(height * 0.1),
            'bottom': int(height * 0.9),
            'left': int(width * 0.1),
            'right': int(width * 0.9),
            'width': int(width * 0.8),
            'height': int(height * 0.8)
        }
        
        # Default features
        features = {
            'center': (width // 2, height // 2),
            'baskets': [
                {'position': (width // 2, int(height * 0.1))},
                {'position': (width // 2, int(height * 0.9))}
            ]
        }
        
        # Default mapping
        mapping = {
            'scale_x': self.court_width / (width * 0.8),
            'scale_y': self.court_length / (height * 0.8),
            'origin_x': int(width * 0.1),
            'origin_y': int(height * 0.9)
        }
        
        return {
            'boundaries': boundaries,
            'features': features,
            'mapping': mapping
        }


# Create a singleton instance
court_detector = CourtDetector()
