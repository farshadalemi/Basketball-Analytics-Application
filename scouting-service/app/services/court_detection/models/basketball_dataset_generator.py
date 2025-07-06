"""
Basketball Court Dataset Generator for Training CNN Keypoint Detection Model.

This module generates synthetic basketball court training data with labeled keypoints
to bootstrap the training process before collecting real-world data.
"""

import numpy as np
import cv2
import json
import os
import random
from typing import List, Tuple, Dict, Any
import logging
from dataclasses import dataclass
from basketball_court_keypoints import BasketballCourtTemplate, BasketballCourtKeypoints

logger = logging.getLogger(__name__)

@dataclass
class SyntheticCourtConfig:
    """Configuration for synthetic court generation."""
    image_width: int = 640
    image_height: int = 480
    court_color_range: Tuple[Tuple[int, int, int], Tuple[int, int, int]] = ((139, 69, 19), (205, 133, 63))  # Brown range
    line_color: Tuple[int, int, int] = (255, 255, 255)  # White lines
    line_thickness: int = 3
    noise_level: float = 0.1
    perspective_variation: float = 0.2
    lighting_variation: float = 0.3

class BasketballDatasetGenerator:
    """
    Generate synthetic basketball court images with labeled keypoints for training.

    This generator creates diverse basketball court images with:
    - Different perspectives and camera angles
    - Various lighting conditions
    - Different court colors and textures
    - Noise and distortions to improve model robustness
    """

    def __init__(self, config: SyntheticCourtConfig = None):
        """Initialize the dataset generator."""
        self.config = config or SyntheticCourtConfig()
        self.template = BasketballCourtTemplate()

    def generate_dataset(self, num_images: int, output_dir: str) -> Dict[str, Any]:
        """
        Generate a complete dataset with images and annotations.

        Args:
            num_images: Number of synthetic images to generate
            output_dir: Directory to save the dataset

        Returns:
            Dictionary with dataset statistics
        """
        # Create output directories
        images_dir = os.path.join(output_dir, "images")
        annotations_dir = os.path.join(output_dir, "annotations")
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(annotations_dir, exist_ok=True)

        dataset_info = {
            "num_images": num_images,
            "image_width": self.config.image_width,
            "image_height": self.config.image_height,
            "keypoints_format": "14_points_x_y",
            "images": []
        }

        logger.info(f"Generating {num_images} synthetic basketball court images...")

        for i in range(num_images):
            # Generate synthetic court image with keypoints
            image, keypoints = self._generate_synthetic_court()

            # Save image
            image_filename = f"court_{i:06d}.jpg"
            image_path = os.path.join(images_dir, image_filename)
            cv2.imwrite(image_path, image)

            # Create annotation
            annotation = {
                "id": i,
                "filename": image_filename,
                "width": self.config.image_width,
                "height": self.config.image_height,
                "keypoints": keypoints.tolist()
            }

            # Save annotation
            annotation_filename = f"court_{i:06d}.json"
            annotation_path = os.path.join(annotations_dir, annotation_filename)
            with open(annotation_path, 'w') as f:
                json.dump(annotation, f, indent=2)

            dataset_info["images"].append(annotation)

            if (i + 1) % 100 == 0:
                logger.info(f"Generated {i + 1}/{num_images} images")

        # Save dataset info
        dataset_info_path = os.path.join(output_dir, "dataset_info.json")
        with open(dataset_info_path, 'w') as f:
            json.dump(dataset_info, f, indent=2)

        logger.info(f"Dataset generation complete. Saved to {output_dir}")
        return dataset_info

    def _generate_synthetic_court(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a single synthetic basketball court image with keypoints.

        Returns:
            Tuple of (image, keypoints) where keypoints is array of 28 values
        """
        # Create base court image
        image = self._create_base_court()

        # Apply perspective transformation
        image, keypoints = self._apply_perspective_transform(image)

        # Add lighting variations
        image = self._apply_lighting_variations(image)

        # Add noise and distortions
        image = self._apply_noise_and_distortions(image)

        return image, keypoints

    def _create_base_court(self) -> np.ndarray:
        """Create a basic basketball court image."""
        # Create court background
        court_color = self._random_court_color()
        image = np.full((self.config.image_height, self.config.image_width, 3), court_color, dtype=np.uint8)

        # Get normalized keypoints and scale to image dimensions
        normalized_keypoints = self.template.get_normalized_keypoints()
        keypoints = normalized_keypoints.reshape(14, 2)

        # Scale keypoints to image dimensions
        keypoints[:, 0] *= self.config.image_width
        keypoints[:, 1] *= self.config.image_height
        keypoints = keypoints.astype(int)

        # Draw court lines
        self._draw_court_lines(image, keypoints)

        return image

    def _random_court_color(self) -> Tuple[int, int, int]:
        """Generate a random court color within the specified range."""
        min_color, max_color = self.config.court_color_range
        color = tuple(
            random.randint(min_color[i], max_color[i]) for i in range(3)
        )
        return color

    def _draw_court_lines(self, image: np.ndarray, keypoints: np.ndarray):
        """Draw basketball court lines on the image."""
        color = self.config.line_color
        thickness = self.config.line_thickness

        # Draw court boundary (corners)
        court_corners = keypoints[:4]  # First 4 points
        cv2.polylines(image, [court_corners], True, color, thickness)

        # Draw free-throw lanes
        # Left free-throw lane
        left_ft = keypoints[4:6]  # Points 5-6
        cv2.line(image, tuple(left_ft[0]), tuple(left_ft[1]), color, thickness)

        # Right free-throw lane
        right_ft = keypoints[6:8]  # Points 7-8
        cv2.line(image, tuple(right_ft[0]), tuple(right_ft[1]), color, thickness)

        # Draw center circle
        center_points = keypoints[8:10]  # Points 9-10
        cv2.line(image, tuple(center_points[0]), tuple(center_points[1]), color, thickness)

        # Draw 3-point arcs (simplified as lines)
        left_3pt = keypoints[10:12]  # Points 11-12
        cv2.line(image, tuple(left_3pt[0]), tuple(left_3pt[1]), color, thickness)

        right_3pt = keypoints[12:14]  # Points 13-14
        cv2.line(image, tuple(right_3pt[0]), tuple(right_3pt[1]), color, thickness)

    def _apply_perspective_transform(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Apply random perspective transformation to simulate different camera angles."""
        h, w = image.shape[:2]

        # Define source points (corners of the image)
        src_points = np.float32([[0, 0], [w, 0], [w, h], [0, h]])

        # Add random perspective variation
        variation = self.config.perspective_variation
        dst_points = src_points.copy()

        # Randomly adjust corner positions
        for i in range(4):
            dst_points[i][0] += random.uniform(-variation * w, variation * w)
            dst_points[i][1] += random.uniform(-variation * h, variation * h)

        # Ensure points stay within reasonable bounds
        dst_points = np.clip(dst_points, [0, 0], [w, h])

        # Apply perspective transformation
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        transformed_image = cv2.warpPerspective(image, matrix, (w, h))

        # Transform keypoints
        normalized_keypoints = self.template.get_normalized_keypoints()
        keypoints = normalized_keypoints.reshape(14, 2)

        # Scale to image dimensions
        keypoints[:, 0] *= w
        keypoints[:, 1] *= h

        # Apply perspective transformation to keypoints
        keypoints_homogeneous = np.column_stack([keypoints, np.ones(14)])
        transformed_keypoints = matrix @ keypoints_homogeneous.T
        transformed_keypoints = transformed_keypoints[:2] / transformed_keypoints[2]
        transformed_keypoints = transformed_keypoints.T.flatten()

        return transformed_image, transformed_keypoints

    def _apply_lighting_variations(self, image: np.ndarray) -> np.ndarray:
        """Apply random lighting variations to the image."""
        # Convert to float for processing
        image_float = image.astype(np.float32)

        # Random brightness adjustment
        brightness_factor = 1.0 + random.uniform(-self.config.lighting_variation, self.config.lighting_variation)
        image_float *= brightness_factor

        # Random contrast adjustment
        contrast_factor = 1.0 + random.uniform(-self.config.lighting_variation * 0.5, self.config.lighting_variation * 0.5)
        mean = np.mean(image_float)
        image_float = (image_float - mean) * contrast_factor + mean

        # Clip values and convert back to uint8
        image_float = np.clip(image_float, 0, 255)
        return image_float.astype(np.uint8)

    def _apply_noise_and_distortions(self, image: np.ndarray) -> np.ndarray:
        """Apply random noise and distortions to improve model robustness."""
        # Add Gaussian noise
        noise = np.random.normal(0, self.config.noise_level * 255, image.shape)
        noisy_image = image.astype(np.float32) + noise
        noisy_image = np.clip(noisy_image, 0, 255).astype(np.uint8)

        # Random blur
        if random.random() < 0.3:  # 30% chance of blur
            kernel_size = random.choice([3, 5])
            noisy_image = cv2.GaussianBlur(noisy_image, (kernel_size, kernel_size), 0)

        return noisy_image

def create_basketball_training_dataset(output_dir: str, num_train: int = 1000, num_val: int = 200):
    """
    Create a complete basketball court training dataset.

    Args:
        output_dir: Directory to save the dataset
        num_train: Number of training images
        num_val: Number of validation images
    """
    generator = BasketballDatasetGenerator()

    # Create training set
    train_dir = os.path.join(output_dir, "train")
    train_info = generator.generate_dataset(num_train, train_dir)

    # Create validation set
    val_dir = os.path.join(output_dir, "val")
    val_info = generator.generate_dataset(num_val, val_dir)

    # Create overall dataset info
    dataset_info = {
        "name": "basketball_court_keypoints",
        "description": "Synthetic basketball court dataset for keypoint detection",
        "num_keypoints": 14,
        "keypoint_names": BasketballCourtTemplate.get_keypoint_names(),
        "train": train_info,
        "val": val_info,
        "total_images": num_train + num_val
    }

    # Save overall dataset info
    with open(os.path.join(output_dir, "dataset.json"), 'w') as f:
        json.dump(dataset_info, f, indent=2)

    logger.info(f"Complete dataset created with {num_train} training and {num_val} validation images")
    return dataset_info