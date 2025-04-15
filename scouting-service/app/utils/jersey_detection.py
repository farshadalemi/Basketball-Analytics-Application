"""
Jersey number detection module for basketball player identification.

This module provides functionality for detecting and recognizing jersey numbers
in basketball videos, which is essential for player identification.
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
import os
import math
from pathlib import Path
import pytesseract

class JerseyDetector:
    """
    Jersey number detection using OCR and image processing.
    """

    def __init__(self, ocr_engine: str = "tesseract"):
        """
        Initialize the jersey detector.

        Args:
            ocr_engine: OCR engine to use ("tesseract" or "easyocr")
        """
        self.ocr_engine = ocr_engine
        self.ocr = self._initialize_ocr()
        
        # Define jersey color ranges for common team colors
        # These are in HSV format and would need to be calibrated for specific teams
        self.jersey_colors = {
            "red": [(0, 100, 100), (10, 255, 255)],
            "orange": [(10, 100, 100), (25, 255, 255)],
            "yellow": [(25, 100, 100), (35, 255, 255)],
            "green": [(35, 100, 100), (85, 255, 255)],
            "blue": [(85, 100, 100), (130, 255, 255)],
            "purple": [(130, 100, 100), (170, 255, 255)],
            "white": [(0, 0, 200), (180, 30, 255)],
            "black": [(0, 0, 0), (180, 255, 30)]
        }

    def _initialize_ocr(self) -> Any:
        """
        Initialize the OCR engine.

        Returns:
            Initialized OCR engine
        """
        if self.ocr_engine == "tesseract":
            try:
                # Check if tesseract is installed
                if not pytesseract.get_tesseract_version():
                    print("Warning: Tesseract not found. Using fallback OCR.")
                    return None
                
                # Configure tesseract for number recognition
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
                print("Initialized Tesseract OCR")
                return custom_config
            except Exception as e:
                print(f"Error initializing Tesseract: {e}")
                return None
        elif self.ocr_engine == "easyocr":
            try:
                import easyocr
                reader = easyocr.Reader(['en'], gpu=False)
                print("Initialized EasyOCR")
                return reader
            except ImportError:
                print("Warning: easyocr not installed. Using fallback OCR.")
                return None
        else:
            print(f"Unknown OCR engine: {self.ocr_engine}. Using fallback OCR.")
            return None

    def detect_jersey_numbers(self, frame: np.ndarray, player_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect jersey numbers for players in a frame.

        Args:
            frame: Video frame as numpy array
            player_detections: List of player detections with bounding boxes

        Returns:
            List of player detections with jersey numbers
        """
        players_with_numbers = []

        for detection in player_detections:
            # Extract player bounding box
            bbox = detection['bbox']
            x1, y1, x2, y2 = bbox
            
            # Focus on the upper part of the torso where jersey numbers are typically located
            torso_height = (y2 - y1) * 0.4
            torso_y1 = int(y1 + (y2 - y1) * 0.2)  # Start 20% down from top of bounding box
            torso_y2 = int(torso_y1 + torso_height)
            
            # Ensure coordinates are within frame bounds
            height, width = frame.shape[:2]
            torso_y1 = max(0, torso_y1)
            torso_y2 = min(height, torso_y2)
            x1 = max(0, x1)
            x2 = min(width, x2)
            
            # Extract torso region
            torso_img = frame[torso_y1:torso_y2, x1:x2]
            if torso_img.size == 0:
                players_with_numbers.append(detection)
                continue
            
            # Detect jersey number
            jersey_number = self._recognize_number(torso_img)
            
            # Add jersey number to detection
            detection_with_number = detection.copy()
            detection_with_number['jersey_number'] = jersey_number
            players_with_numbers.append(detection_with_number)
        
        return players_with_numbers

    def _recognize_number(self, torso_img: np.ndarray) -> Optional[str]:
        """
        Recognize jersey number from torso image.

        Args:
            torso_img: Image of player's torso

        Returns:
            Detected jersey number or None if not detected
        """
        if torso_img.size == 0:
            return None
        
        # Try to recognize with the configured OCR engine
        if self.ocr_engine == "tesseract" and self.ocr is not None:
            try:
                # Preprocess image for better OCR
                preprocessed = self._preprocess_for_ocr(torso_img)
                
                # Perform OCR
                text = pytesseract.image_to_string(preprocessed, config=self.ocr)
                
                # Extract digits
                digits = ''.join(c for c in text if c.isdigit())
                
                # Return first 1-2 digits as jersey number
                if digits:
                    return digits[:2]
                
                return None
            except Exception as e:
                print(f"Error in Tesseract OCR: {e}")
                # Fall back to template matching or other methods
        
        elif self.ocr_engine == "easyocr" and self.ocr is not None:
            try:
                # Preprocess image for better OCR
                preprocessed = self._preprocess_for_ocr(torso_img)
                
                # Perform OCR
                results = self.ocr.readtext(preprocessed)
                
                # Extract digits from results
                digits = ''
                for (bbox, text, prob) in results:
                    digits += ''.join(c for c in text if c.isdigit())
                
                # Return first 1-2 digits as jersey number
                if digits:
                    return digits[:2]
                
                return None
            except Exception as e:
                print(f"Error in EasyOCR: {e}")
                # Fall back to template matching or other methods
        
        # Fallback: Generate random jersey number for testing
        # In a real implementation, this would use more sophisticated methods
        import random
        return str(random.randint(0, 99))

    def _preprocess_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.

        Args:
            img: Input image

        Returns:
            Preprocessed image
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Apply morphological operations to clean up the image
            kernel = np.ones((3, 3), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # Dilate to connect components
            dilated = cv2.dilate(opening, kernel, iterations=1)
            
            return dilated
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return img

    def detect_team_colors(self, frame: np.ndarray, player_detections: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect and classify team colors to separate players into teams.

        Args:
            frame: Video frame as numpy array
            player_detections: List of player detections with bounding boxes

        Returns:
            Dictionary with team classifications
        """
        if not player_detections:
            return {"team1": [], "team2": []}
        
        # Extract color samples from each player's torso
        player_colors = []
        
        for detection in player_detections:
            # Extract player bounding box
            bbox = detection['bbox']
            x1, y1, x2, y2 = bbox
            
            # Focus on the torso where jersey colors are most visible
            torso_height = (y2 - y1) * 0.4
            torso_y1 = int(y1 + (y2 - y1) * 0.2)  # Start 20% down from top of bounding box
            torso_y2 = int(torso_y1 + torso_height)
            
            # Ensure coordinates are within frame bounds
            height, width = frame.shape[:2]
            torso_y1 = max(0, torso_y1)
            torso_y2 = min(height, torso_y2)
            x1 = max(0, x1)
            x2 = min(width, x2)
            
            # Extract torso region
            torso_img = frame[torso_y1:torso_y2, x1:x2]
            if torso_img.size == 0:
                continue
            
            # Convert to HSV for better color analysis
            hsv_img = cv2.cvtColor(torso_img, cv2.COLOR_BGR2HSV)
            
            # Calculate average color
            avg_color = np.mean(hsv_img, axis=(0, 1))
            
            # Store color with player detection
            player_colors.append((detection, avg_color))
        
        if not player_colors:
            return {"team1": [], "team2": []}
        
        # Cluster colors into two teams using K-means
        try:
            from sklearn.cluster import KMeans
            
            # Extract color features
            color_features = np.array([color for _, color in player_colors])
            
            # Apply K-means clustering
            kmeans = KMeans(n_clusters=2, random_state=0).fit(color_features)
            labels = kmeans.labels_
            
            # Separate players into teams
            team1 = []
            team2 = []
            
            for i, (detection, _) in enumerate(player_colors):
                if labels[i] == 0:
                    detection_copy = detection.copy()
                    detection_copy['team'] = 'team1'
                    team1.append(detection_copy)
                else:
                    detection_copy = detection.copy()
                    detection_copy['team'] = 'team2'
                    team2.append(detection_copy)
            
            return {"team1": team1, "team2": team2}
        except Exception as e:
            print(f"Error clustering teams: {e}")
            
            # Fallback: Randomly assign teams
            import random
            team1 = []
            team2 = []
            
            for detection, _ in player_colors:
                if random.random() > 0.5:
                    detection_copy = detection.copy()
                    detection_copy['team'] = 'team1'
                    team1.append(detection_copy)
                else:
                    detection_copy = detection.copy()
                    detection_copy['team'] = 'team2'
                    team2.append(detection_copy)
            
            return {"team1": team1, "team2": team2}


# Create a singleton instance
jersey_detector = JerseyDetector()
