"""
Basketball team classification service using jersey color analysis.

This module provides advanced team classification capabilities using:
- K-means clustering for color analysis
- HSV color space analysis for better color separation
- Spatial analysis for team formation detection
- Machine learning for improved classification accuracy
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import colorsys

logger = logging.getLogger(__name__)


@dataclass
class TeamColors:
    """Data class for storing team color information."""
    primary_color: Tuple[int, int, int]  # RGB
    secondary_color: Optional[Tuple[int, int, int]] = None
    color_name: Optional[str] = None
    confidence: float = 0.0


@dataclass
class TeamClassification:
    """Data class for storing team classification results."""
    team_a_players: List[str]
    team_b_players: List[str]
    team_a_colors: TeamColors
    team_b_colors: TeamColors
    classification_confidence: float
    unclassified_players: Optional[List[str]] = None


class TeamClassifier:
    """
    Advanced basketball team classification using color analysis and machine learning.
    
    This class implements sophisticated team classification that can handle:
    - Various jersey colors and patterns
    - Similar team colors
    - Lighting variations
    - Player occlusion and partial visibility
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the team classifier.
        
        Args:
            config: Configuration dictionary with classification parameters
        """
        self.config = config or {}
        self.min_players_for_classification = self.config.get('min_players', 4)
        self.color_similarity_threshold = self.config.get('color_similarity_threshold', 30)
        
        # Color analysis parameters
        self.jersey_region_ratio = 0.4  # Portion of player bbox to analyze for jersey
        self.color_samples_per_player = 50  # Number of color samples to extract
        
        # Team assignment cache
        self.team_assignments = {}
        self.color_history = []
        
        logger.info("TeamClassifier initialized successfully")
    
    def classify_teams(self, frame: np.ndarray, 
                      player_detections: List[Dict[str, Any]]) -> TeamClassification:
        """
        Classify players into two teams based on jersey colors.
        
        Args:
            frame: Input video frame
            player_detections: List of player detection dictionaries
            
        Returns:
            TeamClassification object with team assignments
        """
        try:
            logger.debug(f"Classifying {len(player_detections)} players into teams")
            
            if len(player_detections) < self.min_players_for_classification:
                logger.warning(f"Insufficient players for classification: {len(player_detections)}")
                return self._create_empty_classification()
            
            # Extract jersey colors for each player
            player_colors = self._extract_player_colors(frame, player_detections)
            
            if len(player_colors) < 2:
                logger.warning("Insufficient color data for classification")
                return self._create_empty_classification()
            
            # Perform color clustering to identify team colors
            team_assignments = self._cluster_players_by_color(player_colors)
            
            # Analyze team colors
            team_a_colors, team_b_colors = self._analyze_team_colors(
                frame, player_detections, team_assignments
            )
            
            # Calculate classification confidence
            confidence = self._calculate_classification_confidence(
                player_colors, team_assignments
            )
            
            # Create classification result
            classification = TeamClassification(
                team_a_players=[p['player_id'] for p in player_detections 
                              if team_assignments.get(p['player_id']) == 'team_a'],
                team_b_players=[p['player_id'] for p in player_detections 
                              if team_assignments.get(p['player_id']) == 'team_b'],
                team_a_colors=team_a_colors,
                team_b_colors=team_b_colors,
                classification_confidence=confidence,
                unclassified_players=[p['player_id'] for p in player_detections 
                                    if team_assignments.get(p['player_id']) not in ['team_a', 'team_b']]
            )
            
            # Update team assignment cache
            self.team_assignments.update(team_assignments)
            
            logger.debug(f"Team classification completed with confidence: {confidence}")
            return classification
            
        except Exception as e:
            logger.error(f"Error in team classification: {str(e)}")
            return self._create_empty_classification()
    
    def _extract_player_colors(self, frame: np.ndarray, 
                              player_detections: List[Dict[str, Any]]) -> Dict[str, List[Tuple[int, int, int]]]:
        """
        Extract dominant colors from each player's jersey region.
        
        Args:
            frame: Input frame
            player_detections: List of player detections
            
        Returns:
            Dictionary mapping player_id to list of RGB colors
        """
        player_colors = {}
        
        for detection in player_detections:
            player_id = detection['player_id']
            bbox = detection['bbox']
            
            # Extract jersey region
            jersey_colors = self._extract_jersey_colors(frame, bbox)
            
            if jersey_colors:
                player_colors[player_id] = jersey_colors
        
        return player_colors
    
    def _extract_jersey_colors(self, frame: np.ndarray, 
                              bbox: Tuple[float, float, float, float]) -> List[Tuple[int, int, int]]:
        """
        Extract colors from a player's jersey region.
        
        Args:
            frame: Input frame
            bbox: Player bounding box (x1, y1, x2, y2)
            
        Returns:
            List of RGB color tuples
        """
        try:
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            x1, y1 = max(0, x1), max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)
            
            if x2 <= x1 or y2 <= y1:
                return []
            
            # Extract player region
            player_region = frame[y1:y2, x1:x2]
            
            # Focus on jersey area (upper torso)
            height = y2 - y1
            jersey_start = int(height * 0.15)  # Skip head area
            jersey_end = int(height * (0.15 + self.jersey_region_ratio))
            
            if jersey_end <= jersey_start:
                return []
            
            jersey_region = player_region[jersey_start:jersey_end, :]
            
            # Convert to HSV for better color analysis
            hsv_region = cv2.cvtColor(jersey_region, cv2.COLOR_BGR2HSV)
            
            # Sample colors from the jersey region
            colors = []
            h, w = jersey_region.shape[:2]
            
            # Create a grid of sample points
            sample_points = []
            for i in range(5):  # 5x5 grid
                for j in range(5):
                    y = int(h * (i + 1) / 6)
                    x = int(w * (j + 1) / 6)
                    sample_points.append((y, x))
            
            # Extract colors from sample points
            for y, x in sample_points:
                if 0 <= y < h and 0 <= x < w:
                    # Get BGR color and convert to RGB
                    bgr_color = jersey_region[y, x]
                    rgb_color = (int(bgr_color[2]), int(bgr_color[1]), int(bgr_color[0]))
                    
                    # Filter out skin tones and very dark/light colors
                    if self._is_valid_jersey_color(rgb_color):
                        colors.append(rgb_color)
            
            return colors
            
        except Exception as e:
            logger.error(f"Error extracting jersey colors: {str(e)}")
            return []
    
    def _is_valid_jersey_color(self, rgb_color: Tuple[int, int, int]) -> bool:
        """
        Check if a color is a valid jersey color (not skin tone, too dark, or too light).
        
        Args:
            rgb_color: RGB color tuple
            
        Returns:
            True if color is valid for jersey analysis
        """
        r, g, b = rgb_color
        
        # Convert to HSV for better analysis
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        h = h * 360  # Convert to degrees
        s = s * 100  # Convert to percentage
        v = v * 100  # Convert to percentage
        
        # Filter out skin tones (hue around 10-40 degrees with moderate saturation)
        if 10 <= h <= 40 and 20 <= s <= 80 and 30 <= v <= 80:
            return False
        
        # Filter out very dark colors (low value)
        if v < 20:
            return False
        
        # Filter out very light/white colors (low saturation, high value)
        if s < 15 and v > 80:
            return False
        
        # Filter out very saturated colors that might be artifacts
        if s > 95:
            return False
        
        return True
    
    def _cluster_players_by_color(self, player_colors: Dict[str, List[Tuple[int, int, int]]]) -> Dict[str, str]:
        """
        Cluster players into teams based on their jersey colors.
        
        Args:
            player_colors: Dictionary mapping player_id to color lists
            
        Returns:
            Dictionary mapping player_id to team assignment
        """
        if len(player_colors) < 2:
            return {}
        
        try:
            # Prepare data for clustering
            player_ids = list(player_colors.keys())
            color_features = []
            
            for player_id in player_ids:
                colors = player_colors[player_id]
                if colors:
                    # Calculate dominant color for each player
                    dominant_color = self._calculate_dominant_color(colors)
                    color_features.append(dominant_color)
                else:
                    # Use neutral color for players without valid colors
                    color_features.append([128, 128, 128])
            
            if len(color_features) < 2:
                return {}
            
            # Perform K-means clustering with k=2 (two teams)
            color_features = np.array(color_features)

            # Standardize features
            scaler = StandardScaler()
            normalized_features = scaler.fit_transform(color_features)

            # Apply K-means clustering
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(normalized_features)

            # Create team assignments
            team_assignments = {}
            for i, player_id in enumerate(player_ids):
                team_label = 'team_a' if cluster_labels[i] == 0 else 'team_b'
                team_assignments[player_id] = team_label

            return team_assignments
            
        except Exception as e:
            logger.error(f"Error in color clustering: {str(e)}")
            return {}
    
    def _calculate_dominant_color(self, colors: List[Tuple[int, int, int]]) -> List[int]:
        """
        Calculate the dominant color from a list of colors.
        
        Args:
            colors: List of RGB color tuples
            
        Returns:
            Dominant color as RGB list
        """
        if not colors:
            return [128, 128, 128]  # Neutral gray
        
        try:
            # Use K-means to find dominant color
            colors_array = np.array(colors)
            
            if len(colors) == 1:
                return colors[0]
            
            # Apply K-means with k=1 to find centroid
            kmeans = KMeans(n_clusters=1, random_state=42, n_init=10)
            kmeans.fit(colors_array)
            
            dominant_color = kmeans.cluster_centers_[0]
            return [int(c) for c in dominant_color]
            
        except Exception as e:
            logger.error(f"Error calculating dominant color: {str(e)}")
            # Fallback to simple average
            avg_color = np.mean(colors, axis=0)
            return [int(c) for c in avg_color]

    def _analyze_team_colors(self, frame: np.ndarray,
                           player_detections: List[Dict[str, Any]],
                           team_assignments: Dict[str, str]) -> Tuple[TeamColors, TeamColors]:
        """
        Analyze and determine the characteristic colors for each team.

        Args:
            frame: Input frame
            player_detections: List of player detections
            team_assignments: Team assignments for each player

        Returns:
            Tuple of TeamColors for team_a and team_b
        """
        team_a_colors = []
        team_b_colors = []

        # Collect colors for each team
        for detection in player_detections:
            player_id = detection['player_id']
            team = team_assignments.get(player_id)

            if team in ['team_a', 'team_b']:
                jersey_colors = self._extract_jersey_colors(frame, detection['bbox'])
                if jersey_colors:
                    if team == 'team_a':
                        team_a_colors.extend(jersey_colors)
                    else:
                        team_b_colors.extend(jersey_colors)

        # Calculate team color characteristics
        team_a_color_info = self._calculate_team_color_info(team_a_colors)
        team_b_color_info = self._calculate_team_color_info(team_b_colors)

        return team_a_color_info, team_b_color_info

    def _calculate_team_color_info(self, colors: List[Tuple[int, int, int]]) -> TeamColors:
        """
        Calculate team color information from a list of colors.

        Args:
            colors: List of RGB color tuples

        Returns:
            TeamColors object with color analysis
        """
        if not colors:
            return TeamColors(primary_color=(128, 128, 128), confidence=0.0)

        try:
            # Find dominant colors using clustering
            colors_array = np.array(colors)

            # Use K-means to find 1-2 dominant colors
            n_clusters = min(2, len(colors))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(colors_array)

            # Get cluster centers (dominant colors)
            dominant_colors = kmeans.cluster_centers_

            # Sort by cluster size (most common first)
            labels = kmeans.labels_
            cluster_sizes = [np.sum(labels == i) for i in range(n_clusters)]
            sorted_indices = np.argsort(cluster_sizes)[::-1]

            primary_color = tuple(int(c) for c in dominant_colors[sorted_indices[0]])
            secondary_color = None

            if len(sorted_indices) > 1:
                secondary_color = tuple(int(c) for c in dominant_colors[sorted_indices[1]])

            # Calculate confidence based on color consistency
            confidence = self._calculate_color_confidence(colors_array, dominant_colors[sorted_indices[0]])

            # Determine color name
            color_name = self._get_color_name(primary_color)

            return TeamColors(
                primary_color=primary_color,
                secondary_color=secondary_color,
                color_name=color_name,
                confidence=confidence
            )

        except Exception as e:
            logger.error(f"Error calculating team color info: {str(e)}")
            return TeamColors(primary_color=(128, 128, 128), confidence=0.0)

    def _calculate_color_confidence(self, colors: np.ndarray, dominant_color: np.ndarray) -> float:
        """
        Calculate confidence score for color classification.

        Args:
            colors: Array of colors
            dominant_color: Dominant color

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            # Calculate distances from dominant color
            distances = np.linalg.norm(colors - dominant_color, axis=1)

            # Calculate confidence based on color consistency
            mean_distance = np.mean(distances)
            max_distance = np.sqrt(3 * 255**2)  # Maximum possible RGB distance

            # Normalize to 0-1 range (lower distance = higher confidence)
            confidence = 1.0 - (mean_distance / max_distance)

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.error(f"Error calculating color confidence: {str(e)}")
            return 0.0

    def _get_color_name(self, rgb_color: Tuple[int, int, int]) -> str:
        """
        Get a human-readable name for an RGB color.

        Args:
            rgb_color: RGB color tuple

        Returns:
            Color name string
        """
        r, g, b = rgb_color

        # Convert to HSV for better color classification
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        h = h * 360  # Convert to degrees
        s = s * 100  # Convert to percentage
        v = v * 100  # Convert to percentage

        # Classify color based on HSV values
        if v < 20:
            return "black"
        elif v > 80 and s < 20:
            return "white"
        elif s < 30:
            return "gray"
        elif 0 <= h < 15 or 345 <= h <= 360:
            return "red"
        elif 15 <= h < 45:
            return "orange"
        elif 45 <= h < 75:
            return "yellow"
        elif 75 <= h < 150:
            return "green"
        elif 150 <= h < 210:
            return "cyan"
        elif 210 <= h < 270:
            return "blue"
        elif 270 <= h < 330:
            return "purple"
        elif 330 <= h < 345:
            return "pink"
        else:
            return "unknown"

    def _calculate_classification_confidence(self, player_colors: Dict[str, List[Tuple[int, int, int]]],
                                           team_assignments: Dict[str, str]) -> float:
        """
        Calculate overall confidence for team classification.

        Args:
            player_colors: Player color data
            team_assignments: Team assignments

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            if not team_assignments:
                return 0.0

            # Count players in each team
            team_a_count = sum(1 for team in team_assignments.values() if team == 'team_a')
            team_b_count = sum(1 for team in team_assignments.values() if team == 'team_b')

            # Confidence is higher when teams are more balanced
            total_players = team_a_count + team_b_count
            if total_players == 0:
                return 0.0

            balance_score = 1.0 - abs(team_a_count - team_b_count) / total_players

            # Additional confidence based on color separation
            separation_score = self._calculate_color_separation_score(player_colors, team_assignments)

            # Combine scores
            overall_confidence = (balance_score + separation_score) / 2.0

            return max(0.0, min(1.0, overall_confidence))

        except Exception as e:
            logger.error(f"Error calculating classification confidence: {str(e)}")
            return 0.0

    def _calculate_color_separation_score(self, player_colors: Dict[str, List[Tuple[int, int, int]]],
                                        team_assignments: Dict[str, str]) -> float:
        """
        Calculate how well separated the team colors are.

        Args:
            player_colors: Player color data
            team_assignments: Team assignments

        Returns:
            Separation score between 0.0 and 1.0
        """
        try:
            team_a_colors = []
            team_b_colors = []

            # Collect colors for each team
            for player_id, colors in player_colors.items():
                team = team_assignments.get(player_id)
                if team == 'team_a':
                    team_a_colors.extend(colors)
                elif team == 'team_b':
                    team_b_colors.extend(colors)

            if not team_a_colors or not team_b_colors:
                return 0.0

            # Calculate average colors for each team
            avg_color_a = np.mean(team_a_colors, axis=0)
            avg_color_b = np.mean(team_b_colors, axis=0)

            # Calculate distance between team colors
            color_distance = np.linalg.norm(avg_color_a - avg_color_b)
            max_distance = np.sqrt(3 * 255**2)  # Maximum possible RGB distance

            # Normalize to 0-1 range
            separation_score = color_distance / max_distance

            return max(0.0, min(1.0, separation_score))

        except Exception as e:
            logger.error(f"Error calculating color separation score: {str(e)}")
            return 0.0

    def _create_empty_classification(self) -> TeamClassification:
        """
        Create an empty team classification result.

        Returns:
            Empty TeamClassification object
        """
        return TeamClassification(
            team_a_players=[],
            team_b_players=[],
            team_a_colors=TeamColors(primary_color=(128, 128, 128), confidence=0.0),
            team_b_colors=TeamColors(primary_color=(128, 128, 128), confidence=0.0),
            classification_confidence=0.0,
            unclassified_players=[]
        )

    def get_cached_team_assignment(self, player_id: str) -> Optional[str]:
        """
        Get cached team assignment for a player.

        Args:
            player_id: Player identifier

        Returns:
            Team assignment ('team_a' or 'team_b') or None
        """
        return self.team_assignments.get(player_id)

    def clear_cache(self):
        """Clear team assignment cache."""
        self.team_assignments.clear()
        self.color_history.clear()
        logger.info("Team classifier cache cleared")
