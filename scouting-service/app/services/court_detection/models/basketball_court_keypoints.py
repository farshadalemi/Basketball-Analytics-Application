"""
Basketball Court Keypoints Detection using Transfer Learning from Tennis Court Detection.

This module defines the basketball court keypoints template and provides utilities
for basketball court detection using a CNN-based approach similar to tennis court detection.

Basketball Court Keypoints (14 points):
1. Top-left corner
2. Top-right corner
3. Bottom-left corner
4. Bottom-right corner
5. Left free-throw line top
6. Left free-throw line bottom
7. Right free-throw line top
8. Right free-throw line bottom
9. Center circle top
10. Center circle bottom
11. Left 3-point arc top
12. Left 3-point arc bottom
13. Right 3-point arc top
14. Right 3-point arc bottom
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional, Dict, Any
import logging
from dataclasses import dataclass

# Optional PyTorch imports
try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
    from torchvision import models
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    logging.warning("PyTorch not available. CNN-based court detection will be disabled.")

logger = logging.getLogger(__name__)

@dataclass
class BasketballCourtKeypoints:
    """Basketball court keypoints data structure."""
    keypoints: np.ndarray  # 14 keypoints, each with (x, y) coordinates
    confidence: float
    detection_method: str = "cnn_keypoints"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'keypoints': self.keypoints.tolist() if self.keypoints is not None else None,
            'confidence': self.confidence,
            'detection_method': self.detection_method,
            'num_keypoints': len(self.keypoints) // 2 if self.keypoints is not None else 0
        }

class BasketballCourtTemplate:
    """
    Basketball court template with standard keypoints.

    Based on NBA court dimensions:
    - Court: 94 feet long × 50 feet wide
    - Free throw lane: 16 feet wide
    - 3-point line: 23'9" from basket
    - Center circle: 12 feet diameter
    """

    # Standard NBA court dimensions (in feet)
    COURT_LENGTH = 94.0
    COURT_WIDTH = 50.0
    FREE_THROW_LANE_WIDTH = 16.0
    THREE_POINT_DISTANCE = 23.75  # 23'9"
    CENTER_CIRCLE_RADIUS = 6.0

    @classmethod
    def get_normalized_keypoints(cls) -> np.ndarray:
        """
        Get normalized basketball court keypoints (0-1 range).

        Returns:
            np.ndarray: 28 values (14 keypoints × 2 coordinates each)
        """
        # Define keypoints in normalized coordinates (0-1)
        keypoints = np.array([
            # Court corners
            [0.0, 0.0],      # 1. Top-left corner
            [1.0, 0.0],      # 2. Top-right corner
            [0.0, 1.0],      # 3. Bottom-left corner
            [1.0, 1.0],      # 4. Bottom-right corner

            # Free-throw lines (left side)
            [0.19, 0.2],     # 5. Left free-throw line top
            [0.19, 0.8],     # 6. Left free-throw line bottom

            # Free-throw lines (right side)
            [0.81, 0.2],     # 7. Right free-throw line top
            [0.81, 0.8],     # 8. Right free-throw line bottom

            # Center circle
            [0.5, 0.35],     # 9. Center circle top
            [0.5, 0.65],     # 10. Center circle bottom

            # 3-point arc (left side)
            [0.25, 0.15],    # 11. Left 3-point arc top
            [0.25, 0.85],    # 12. Left 3-point arc bottom

            # 3-point arc (right side)
            [0.75, 0.15],    # 13. Right 3-point arc top
            [0.75, 0.85],    # 14. Right 3-point arc bottom
        ], dtype=np.float32)

        return keypoints.flatten()  # Return as 1D array of 28 values

    @classmethod
    def get_keypoint_names(cls) -> List[str]:
        """Get descriptive names for each keypoint."""
        return [
            "Top-left corner",
            "Top-right corner",
            "Bottom-left corner",
            "Bottom-right corner",
            "Left free-throw line top",
            "Left free-throw line bottom",
            "Right free-throw line top",
            "Right free-throw line bottom",
            "Center circle top",
            "Center circle bottom",
            "Left 3-point arc top",
            "Left 3-point arc bottom",
            "Right 3-point arc top",
            "Right 3-point arc bottom"
        ]

    @classmethod
    def validate_keypoints(cls, keypoints: np.ndarray) -> bool:
        """
        Validate that keypoints form a reasonable basketball court.

        Args:
            keypoints: Array of 28 values (14 keypoints × 2 coordinates)

        Returns:
            bool: True if keypoints are valid
        """
        if len(keypoints) != 28:
            return False

        # Reshape to (14, 2) for easier validation
        points = keypoints.reshape(14, 2)

        # Basic validation checks
        try:
            # Check that corners form a rectangle
            corners = points[:4]  # First 4 points are corners

            # Top-left should be at minimum x,y
            # Top-right should be at maximum x, minimum y
            # Bottom-left should be at minimum x, maximum y
            # Bottom-right should be at maximum x,y

            if not (corners[0][0] < corners[1][0]):  # Top-left x < Top-right x
                return False
            if not (corners[0][1] < corners[2][1]):  # Top-left y < Bottom-left y
                return False

            # Check that free-throw lines are inside court
            ft_lines = points[4:8]  # Free-throw line points
            for point in ft_lines:
                if not (0.1 < point[0] < 0.9 and 0.1 < point[1] < 0.9):
                    return False

            return True

        except Exception as e:
            logger.warning(f"Keypoint validation error: {e}")
            return False

if PYTORCH_AVAILABLE:
    class BasketballCourtKeypointDetector(nn.Module):
        """
        Basketball court keypoint detection model using transfer learning from tennis court detection.

        Architecture:
        - ResNet-50 backbone (pretrained on ImageNet)
        - Custom fully connected layer for 14 keypoints (28 outputs)
        - Can be initialized with tennis court weights for transfer learning
        """
        pass
else:
    class BasketballCourtKeypointDetector:
        """
        Basketball court keypoint detection model using transfer learning from tennis court detection.

        Architecture:
        - ResNet-50 backbone (pretrained on ImageNet)
        - Custom fully connected layer for 14 keypoints (28 outputs)
        - Can be initialized with tennis court weights for transfer learning
        """

        def __init__(self, pretrained: bool = True, tennis_weights_path: Optional[str] = None):
            """
            Initialize the basketball court keypoint detector.

            Args:
                pretrained: Whether to use ImageNet pretrained weights
                tennis_weights_path: Path to tennis court model weights for transfer learning
            """
            if not PYTORCH_AVAILABLE:
                raise ImportError("PyTorch is not available. Cannot initialize CNN-based court detector.")

            # Initialize as PyTorch module only if PyTorch is available
            super(BasketballCourtKeypointDetector, self).__init__()

            # Load ResNet-50 backbone
            self.backbone = models.resnet50(pretrained=pretrained)

            # Replace the final fully connected layer
            # Tennis model outputs 14*2=28 values, same as basketball
            self.backbone.fc = nn.Linear(self.backbone.fc.in_features, 14 * 2)

            # Load tennis court weights if provided
            if tennis_weights_path:
                self._load_tennis_weights(tennis_weights_path)

            # Image preprocessing transforms
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])

        def _load_tennis_weights(self, weights_path: str):
            """Load tennis court model weights for transfer learning."""
            try:
                # Load tennis court weights
                tennis_state_dict = torch.load(weights_path, map_location='cpu')

                # Load the weights (they should be compatible since same architecture)
                self.backbone.load_state_dict(tennis_state_dict)

                logger.info(f"Successfully loaded tennis court weights from {weights_path}")

            except Exception as e:
                logger.warning(f"Could not load tennis weights: {e}. Using random initialization.")

        def forward(self, x):
            """Forward pass through the network."""
            return self.backbone(x)

        def predict(self, image: np.ndarray) -> BasketballCourtKeypoints:
            """
            Predict basketball court keypoints from an image.

            Args:
                image: Input image as numpy array (BGR format)

            Returns:
                BasketballCourtKeypoints object with detected keypoints
            """
            try:
                # Convert BGR to RGB
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # Apply transforms
                image_tensor = self.transform(image_rgb).unsqueeze(0)

                # Get original image dimensions for scaling
                original_h, original_w = image.shape[:2]

                # Predict keypoints
                self.eval()
                with torch.no_grad():
                    outputs = self(image_tensor)
                    keypoints = outputs.squeeze().cpu().numpy()

                # Scale keypoints from normalized coordinates to image coordinates
                keypoints[::2] *= original_w / 224.0   # Scale x coordinates
                keypoints[1::2] *= original_h / 224.0  # Scale y coordinates

                # Validate keypoints
                if BasketballCourtTemplate.validate_keypoints(keypoints):
                    confidence = 0.8  # High confidence for valid keypoints
                else:
                    confidence = 0.3  # Lower confidence for potentially invalid keypoints

                return BasketballCourtKeypoints(
                    keypoints=keypoints,
                    confidence=confidence,
                    detection_method="cnn_keypoints"
                )

            except Exception as e:
                logger.error(f"Error in basketball court keypoint prediction: {e}")
                return BasketballCourtKeypoints(
                    keypoints=np.zeros(28),
                    confidence=0.0,
                    detection_method="error"
                )

        def draw_keypoints(self, image: np.ndarray, keypoints: np.ndarray) -> np.ndarray:
            """
            Draw keypoints on the image for visualization.

            Args:
                image: Input image
                keypoints: Array of 28 keypoint coordinates

            Returns:
                Image with keypoints drawn
            """
            result_image = image.copy()
            keypoint_names = BasketballCourtTemplate.get_keypoint_names()

            # Reshape keypoints to (14, 2)
            points = keypoints.reshape(14, 2)

            # Draw keypoints
            for i, (x, y) in enumerate(points):
                x, y = int(x), int(y)

                # Draw circle for keypoint
                cv2.circle(result_image, (x, y), 5, (0, 0, 255), -1)

                # Draw keypoint number
                cv2.putText(result_image, str(i+1), (x+10, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Draw court lines connecting keypoints
            self._draw_court_lines(result_image, points)

            return result_image

        def _draw_court_lines(self, image: np.ndarray, points: np.ndarray):
            """Draw basketball court lines connecting the keypoints."""
            # Convert points to integers
            points = points.astype(int)

            # Draw court boundary (corners)
            court_corners = points[:4]  # First 4 points
            cv2.polylines(image, [court_corners], True, (0, 255, 0), 2)

            # Draw free-throw lanes
            # Left free-throw lane
            left_ft = points[4:6]  # Points 5-6
            cv2.line(image, tuple(left_ft[0]), tuple(left_ft[1]), (255, 0, 0), 2)

            # Right free-throw lane
            right_ft = points[6:8]  # Points 7-8
            cv2.line(image, tuple(right_ft[0]), tuple(right_ft[1]), (255, 0, 0), 2)

            # Draw center circle
            center_points = points[8:10]  # Points 9-10
            cv2.line(image, tuple(center_points[0]), tuple(center_points[1]), (0, 255, 255), 2)

            # Draw 3-point arcs (simplified as lines)
            left_3pt = points[10:12]  # Points 11-12
            cv2.line(image, tuple(left_3pt[0]), tuple(left_3pt[1]), (255, 255, 0), 2)

            right_3pt = points[12:14]  # Points 13-14
            cv2.line(image, tuple(right_3pt[0]), tuple(right_3pt[1]), (255, 255, 0), 2)