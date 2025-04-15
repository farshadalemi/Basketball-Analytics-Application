"""Player detection and tracking for basketball videos."""
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

from app.core.logging import logger


class PlayerDetector:
    """Player detection using YOLOv8 or fallback methods."""
    
    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize the player detector.
        
        Args:
            confidence_threshold: Confidence threshold for detections
        """
        self.confidence_threshold = confidence_threshold
        self.model = None
        
        # Try to load YOLOv8
        try:
            from ultralytics import YOLO
            self.model = YOLO('yolov8n.pt')  # Use smaller model to start
            logger.info("Initialized YOLOv8 model for player detection")
        except ImportError:
            logger.warning("YOLOv8 not available. Using fallback detection.")
            self.model = None
    
    def detect_players(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect players in a frame.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            List of player detections with bounding boxes
        """
        if self.model is None:
            return self._fallback_detection(frame)
        
        try:
            # Run YOLOv8 detection
            results = self.model(frame, classes=[0])  # Class 0 is person
            players = []
            
            for i, detection in enumerate(results[0].boxes.data):
                x1, y1, x2, y2, conf, cls = detection
                if conf > self.confidence_threshold:
                    players.append({
                        'id': i,
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': float(conf),
                        'team': 'unknown'  # Will be determined later
                    })
            
            logger.debug(f"Detected {len(players)} players with YOLOv8")
            return players
        except Exception as e:
            logger.error(f"Error in YOLOv8 player detection: {e}")
            return self._fallback_detection(frame)
    
    def _fallback_detection(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Fallback player detection using OpenCV HOG detector.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            List of player detections with bounding boxes
        """
        # Initialize HOG detector
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # Detect people
        boxes, weights = hog.detectMultiScale(
            frame, 
            winStride=(8, 8),
            padding=(4, 4),
            scale=1.05
        )
        
        players = []
        for i, (box, weight) in enumerate(zip(boxes, weights)):
            x, y, w, h = box
            if weight > self.confidence_threshold:
                players.append({
                    'id': i,
                    'bbox': [float(x), float(y), float(x + w), float(y + h)],
                    'confidence': float(weight),
                    'team': 'unknown'
                })
        
        logger.debug(f"Detected {len(players)} players with HOG detector")
        return players
    
    def assign_teams(self, players: List[Dict[str, Any]], frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Assign teams to detected players based on jersey colors.
        
        Args:
            players: List of player detections
            frame: Video frame as numpy array
            
        Returns:
            Updated list of player detections with team assignments
        """
        # Simple team assignment based on jersey color clustering
        if not players:
            return players
        
        # Extract jersey color for each player
        jersey_colors = []
        for player in players:
            x1, y1, x2, y2 = player['bbox']
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # Ensure coordinates are within frame bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1] - 1, x2)
            y2 = min(frame.shape[0] - 1, y2)
            
            # Skip if bounding box is invalid
            if x1 >= x2 or y1 >= y2:
                jersey_colors.append(None)
                continue
            
            # Extract upper body region (assume jersey is in upper half of body)
            upper_y = y1 + (y2 - y1) // 3
            jersey_region = frame[y1:upper_y, x1:x2]
            
            # Skip if region is empty
            if jersey_region.size == 0:
                jersey_colors.append(None)
                continue
            
            # Calculate average color in HSV space
            jersey_hsv = cv2.cvtColor(jersey_region, cv2.COLOR_BGR2HSV)
            avg_color = np.mean(jersey_hsv, axis=(0, 1))
            
            jersey_colors.append(avg_color)
        
        # Filter out None values
        valid_colors = [c for c in jersey_colors if c is not None]
        if len(valid_colors) < 2:
            # Not enough valid colors to cluster
            return players
        
        # Cluster colors into two teams using K-means
        valid_colors_array = np.array(valid_colors, dtype=np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, _ = cv2.kmeans(valid_colors_array, 2, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Assign teams based on clusters
        team_idx = 0
        for i, player in enumerate(players):
            if jersey_colors[i] is not None:
                idx = valid_colors.index(jersey_colors[i])
                team = 'team_a' if labels[idx][0] == 0 else 'team_b'
                player['team'] = team
        
        logger.debug(f"Assigned teams to {len(players)} players")
        return players


# Create a singleton instance
player_detector = PlayerDetector()
