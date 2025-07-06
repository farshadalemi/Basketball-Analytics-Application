"""
Basketball Court Keypoint Detection Training Pipeline.

This module provides training functionality for the basketball court keypoint detection model
using transfer learning from tennis court detection.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import cv2
import numpy as np
import json
import os
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from basketball_court_keypoints import BasketballCourtKeypointDetector, BasketballCourtTemplate
from basketball_dataset_generator import create_basketball_training_dataset

logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Configuration for training the basketball court keypoint detection model."""
    batch_size: int = 8
    learning_rate: float = 1e-4
    num_epochs: int = 50
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    save_interval: int = 10
    validation_interval: int = 5
    early_stopping_patience: int = 10
    weight_decay: float = 1e-4

class BasketballCourtDataset(Dataset):
    """
    PyTorch Dataset for basketball court keypoint detection.

    Compatible with the tennis court training format for easy transfer learning.
    """

    def __init__(self, data_dir: str, split: str = "train"):
        """
        Initialize the dataset.

        Args:
            data_dir: Directory containing the dataset
            split: Either "train" or "val"
        """
        self.data_dir = data_dir
        self.split = split
        self.images_dir = os.path.join(data_dir, split, "images")
        self.annotations_dir = os.path.join(data_dir, split, "annotations")

        # Load dataset info
        dataset_info_path = os.path.join(data_dir, split, "dataset_info.json")
        with open(dataset_info_path, 'r') as f:
            self.dataset_info = json.load(f)

        self.annotations = self.dataset_info["images"]

        # Image preprocessing transforms (same as tennis court model)
        self.transforms = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def __len__(self):
        return len(self.annotations)

    def __getitem__(self, idx):
        """Get a single training sample."""
        annotation = self.annotations[idx]

        # Load image
        image_path = os.path.join(self.images_dir, annotation["filename"])
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Get original dimensions
        original_h, original_w = image.shape[:2]

        # Apply transforms
        image_tensor = self.transforms(image)

        # Load keypoints
        keypoints = np.array(annotation["keypoints"], dtype=np.float32)

        # Normalize keypoints to 224x224 (model input size)
        keypoints[::2] *= 224.0 / original_w   # Scale x coordinates
        keypoints[1::2] *= 224.0 / original_h  # Scale y coordinates

        keypoints_tensor = torch.from_numpy(keypoints)

        return image_tensor, keypoints_tensor

class BasketballCourtTrainer:
    """
    Trainer class for basketball court keypoint detection model.
    """

    def __init__(self, config: TrainingConfig, tennis_weights_path: Optional[str] = None):
        """
        Initialize the trainer.

        Args:
            config: Training configuration
            tennis_weights_path: Path to tennis court model weights for transfer learning
        """
        self.config = config
        self.device = torch.device(config.device)

        # Initialize model with transfer learning
        self.model = BasketballCourtKeypointDetector(
            pretrained=True,
            tennis_weights_path=tennis_weights_path
        ).to(self.device)

        # Loss function (MSE for keypoint regression)
        self.criterion = nn.MSELoss()

        # Optimizer
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )

        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', patience=5, factor=0.5
        )

        # Training metrics
        self.train_losses = []
        self.val_losses = []
        self.best_val_loss = float('inf')
        self.epochs_without_improvement = 0

    def train(self, train_dataset: BasketballCourtDataset, val_dataset: BasketballCourtDataset,
              save_dir: str) -> Dict:
        """
        Train the basketball court keypoint detection model.

        Args:
            train_dataset: Training dataset
            val_dataset: Validation dataset
            save_dir: Directory to save model checkpoints

        Returns:
            Dictionary with training statistics
        """
        os.makedirs(save_dir, exist_ok=True)

        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=2
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=2
        )

        logger.info(f"Starting training on {self.device}")
        logger.info(f"Training samples: {len(train_dataset)}")
        logger.info(f"Validation samples: {len(val_dataset)}")

        for epoch in range(self.config.num_epochs):
            # Training phase
            train_loss = self._train_epoch(train_loader, epoch)
            self.train_losses.append(train_loss)

            # Validation phase
            if epoch % self.config.validation_interval == 0:
                val_loss = self._validate_epoch(val_loader, epoch)
                self.val_losses.append(val_loss)

                # Learning rate scheduling
                self.scheduler.step(val_loss)

                # Early stopping check
                if val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    self.epochs_without_improvement = 0

                    # Save best model
                    best_model_path = os.path.join(save_dir, "best_model.pth")
                    torch.save(self.model.state_dict(), best_model_path)
                    logger.info(f"New best model saved with validation loss: {val_loss:.6f}")
                else:
                    self.epochs_without_improvement += 1

                # Early stopping
                if self.epochs_without_improvement >= self.config.early_stopping_patience:
                    logger.info(f"Early stopping triggered after {epoch + 1} epochs")
                    break

            # Save checkpoint
            if epoch % self.config.save_interval == 0:
                checkpoint_path = os.path.join(save_dir, f"checkpoint_epoch_{epoch}.pth")
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'train_loss': train_loss,
                    'val_loss': val_loss if epoch % self.config.validation_interval == 0 else None
                }, checkpoint_path)

        # Save final model
        final_model_path = os.path.join(save_dir, "final_model.pth")
        torch.save(self.model.state_dict(), final_model_path)

        # Save training statistics
        stats = {
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'best_val_loss': self.best_val_loss,
            'total_epochs': len(self.train_losses)
        }

        stats_path = os.path.join(save_dir, "training_stats.json")
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)

        logger.info("Training completed!")
        return stats

    def _train_epoch(self, train_loader: DataLoader, epoch: int) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        num_batches = len(train_loader)

        for batch_idx, (images, keypoints) in enumerate(train_loader):
            images = images.to(self.device)
            keypoints = keypoints.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = self.criterion(outputs, keypoints)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

            if batch_idx % 10 == 0:
                logger.debug(f"Epoch {epoch}, Batch {batch_idx}/{num_batches}, Loss: {loss.item():.6f}")

        avg_loss = total_loss / num_batches
        logger.info(f"Epoch {epoch} - Training Loss: {avg_loss:.6f}")
        return avg_loss

    def _validate_epoch(self, val_loader: DataLoader, epoch: int) -> float:
        """Validate for one epoch."""
        self.model.eval()
        total_loss = 0.0
        num_batches = len(val_loader)

        with torch.no_grad():
            for images, keypoints in val_loader:
                images = images.to(self.device)
                keypoints = keypoints.to(self.device)

                outputs = self.model(images)
                loss = self.criterion(outputs, keypoints)
                total_loss += loss.item()

        avg_loss = total_loss / num_batches
        logger.info(f"Epoch {epoch} - Validation Loss: {avg_loss:.6f}")
        return avg_loss

def train_basketball_court_model(
    dataset_dir: str,
    tennis_weights_path: Optional[str] = None,
    output_dir: str = "basketball_court_model",
    config: Optional[TrainingConfig] = None
) -> Dict:
    """
    Complete training pipeline for basketball court keypoint detection.

    Args:
        dataset_dir: Directory containing the training dataset
        tennis_weights_path: Path to tennis court model weights for transfer learning
        output_dir: Directory to save the trained model
        config: Training configuration

    Returns:
        Training statistics
    """
    if config is None:
        config = TrainingConfig()

    # Create datasets
    train_dataset = BasketballCourtDataset(dataset_dir, "train")
    val_dataset = BasketballCourtDataset(dataset_dir, "val")

    # Initialize trainer
    trainer = BasketballCourtTrainer(config, tennis_weights_path)

    # Train the model
    stats = trainer.train(train_dataset, val_dataset, output_dir)

    return stats

def create_and_train_basketball_model(
    tennis_weights_path: Optional[str] = None,
    num_train_images: int = 1000,
    num_val_images: int = 200,
    output_dir: str = "basketball_court_training"
) -> Dict:
    """
    Complete pipeline: generate dataset and train basketball court model.

    Args:
        tennis_weights_path: Path to tennis court model weights
        num_train_images: Number of training images to generate
        num_val_images: Number of validation images to generate
        output_dir: Directory for dataset and model output

    Returns:
        Training statistics
    """
    # Create dataset
    dataset_dir = os.path.join(output_dir, "dataset")
    logger.info("Generating synthetic basketball court dataset...")
    create_basketball_training_dataset(dataset_dir, num_train_images, num_val_images)

    # Train model
    model_dir = os.path.join(output_dir, "model")
    logger.info("Training basketball court keypoint detection model...")
    stats = train_basketball_court_model(dataset_dir, tennis_weights_path, model_dir)

    logger.info("Basketball court model training pipeline completed!")
    return stats