"""
Player analysis utilities.

This module provides algorithms for analyzing player performance and characteristics.
"""
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
import math


class PlayerMovementAnalysis:
    """
    Analysis of player movement patterns and tendencies.
    """
    
    def __init__(self, court_width: float = 50, court_length: float = 94):
        """
        Initialize the player movement analysis.
        
        Args:
            court_width: Width of the basketball court in feet
            court_length: Length of the basketball court in feet
        """
        self.court_width = court_width
        self.court_length = court_length
        
    def analyze_movement(self, player_tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze player movement patterns.
        
        Args:
            player_tracks: List of player tracking data points
            
        Returns:
            Movement analysis results
        """
        if not player_tracks:
            return {
                'total_distance': 0,
                'average_speed': 0,
                'max_speed': 0,
                'heatmap': None,
                'common_locations': [],
                'directional_tendencies': {}
            }
        
        # Extract positions and timestamps
        positions = [(track['position'][0], track['position'][1]) for track in player_tracks if 'position' in track]
        timestamps = [track.get('timestamp', 0) for track in player_tracks if 'position' in track]
        
        if not positions or len(positions) < 2:
            return {
                'total_distance': 0,
                'average_speed': 0,
                'max_speed': 0,
                'heatmap': None,
                'common_locations': [],
                'directional_tendencies': {}
            }
        
        # Calculate distances between consecutive positions
        distances = []
        speeds = []
        directions = []
        
        for i in range(1, len(positions)):
            x1, y1 = positions[i-1]
            x2, y2 = positions[i]
            t1 = timestamps[i-1]
            t2 = timestamps[i]
            
            # Calculate distance
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            distances.append(distance)
            
            # Calculate speed (distance / time)
            time_diff = t2 - t1
            if time_diff > 0:
                speed = distance / time_diff
                speeds.append(speed)
            
            # Calculate direction
            if distance > 0:
                dx = x2 - x1
                dy = y2 - y1
                angle = math.degrees(math.atan2(dy, dx))
                directions.append(angle)
        
        # Calculate total distance and average speed
        total_distance = sum(distances)
        average_speed = sum(speeds) / len(speeds) if speeds else 0
        max_speed = max(speeds) if speeds else 0
        
        # Generate heatmap (simplified as a list of positions)
        heatmap = positions
        
        # Find common locations (cluster positions)
        common_locations = self._cluster_positions(positions)
        
        # Analyze directional tendencies
        directional_tendencies = self._analyze_directions(directions)
        
        return {
            'total_distance': total_distance,
            'average_speed': average_speed,
            'max_speed': max_speed,
            'heatmap': heatmap,
            'common_locations': common_locations,
            'directional_tendencies': directional_tendencies
        }
    
    def _cluster_positions(self, positions: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """
        Cluster positions to find common locations.
        
        Args:
            positions: List of (x, y) positions
            
        Returns:
            List of common locations with their properties
        """
        # In a real implementation, we would use a clustering algorithm like K-means
        # For now, simulate clustering by dividing the court into zones
        
        # Define zones
        zones = [
            {'name': 'Left Corner', 'x_range': (0, 10), 'y_range': (0, 10)},
            {'name': 'Right Corner', 'x_range': (40, 50), 'y_range': (0, 10)},
            {'name': 'Top of Key', 'x_range': (20, 30), 'y_range': (15, 25)},
            {'name': 'Left Wing', 'x_range': (10, 20), 'y_range': (15, 25)},
            {'name': 'Right Wing', 'x_range': (30, 40), 'y_range': (15, 25)},
            {'name': 'Paint', 'x_range': (17, 33), 'y_range': (0, 19)},
            {'name': 'Top of Arc', 'x_range': (20, 30), 'y_range': (25, 35)}
        ]
        
        # Count positions in each zone
        zone_counts = {zone['name']: 0 for zone in zones}
        
        for x, y in positions:
            for zone in zones:
                x_min, x_max = zone['x_range']
                y_min, y_max = zone['y_range']
                
                if x_min <= x < x_max and y_min <= y < y_max:
                    zone_counts[zone['name']] += 1
                    break
        
        # Convert to percentage and sort by frequency
        total_positions = len(positions)
        zone_percentages = []
        
        for zone_name, count in zone_counts.items():
            if total_positions > 0:
                percentage = (count / total_positions) * 100
                zone_percentages.append({
                    'zone': zone_name,
                    'percentage': percentage,
                    'count': count
                })
        
        # Sort by percentage (descending)
        zone_percentages.sort(key=lambda x: x['percentage'], reverse=True)
        
        return zone_percentages
    
    def _analyze_directions(self, directions: List[float]) -> Dict[str, float]:
        """
        Analyze directional tendencies.
        
        Args:
            directions: List of movement directions in degrees
            
        Returns:
            Directional tendencies as percentages
        """
        if not directions:
            return {
                'north': 0,
                'northeast': 0,
                'east': 0,
                'southeast': 0,
                'south': 0,
                'southwest': 0,
                'west': 0,
                'northwest': 0
            }
        
        # Define direction ranges
        direction_ranges = {
            'north': (-22.5, 22.5),
            'northeast': (22.5, 67.5),
            'east': (67.5, 112.5),
            'southeast': (112.5, 157.5),
            'south': (157.5, -157.5),
            'southwest': (-157.5, -112.5),
            'west': (-112.5, -67.5),
            'northwest': (-67.5, -22.5)
        }
        
        # Count directions in each range
        direction_counts = {direction: 0 for direction in direction_ranges}
        
        for angle in directions:
            for direction, (min_angle, max_angle) in direction_ranges.items():
                if min_angle <= angle < max_angle:
                    direction_counts[direction] += 1
                    break
        
        # Convert to percentages
        total_directions = len(directions)
        direction_percentages = {}
        
        for direction, count in direction_counts.items():
            if total_directions > 0:
                percentage = (count / total_directions) * 100
                direction_percentages[direction] = percentage
        
        return direction_percentages


class PlayerPerformanceAnalysis:
    """
    Analysis of player performance metrics and tendencies.
    """
    
    def __init__(self):
        """Initialize the player performance analysis."""
        pass
    
    def analyze_performance(self, player_data: Dict[str, Any], shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze player performance based on tracking data and shots.
        
        Args:
            player_data: Player tracking and identification data
            shots: List of shots taken by the player
            
        Returns:
            Performance analysis results
        """
        # Filter shots for this player
        player_shots = [shot for shot in shots if shot.get('player_id') == player_data.get('id')]
        
        # Basic shooting stats
        shooting_stats = self._analyze_shooting(player_shots)
        
        # Offensive tendencies
        offensive_tendencies = self._analyze_offensive_tendencies(player_data, player_shots)
        
        # Defensive tendencies
        defensive_tendencies = self._analyze_defensive_tendencies(player_data)
        
        # Physical attributes
        physical_attributes = self._analyze_physical_attributes(player_data)
        
        return {
            'shooting_stats': shooting_stats,
            'offensive_tendencies': offensive_tendencies,
            'defensive_tendencies': defensive_tendencies,
            'physical_attributes': physical_attributes
        }
    
    def _analyze_shooting(self, shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze shooting performance.
        
        Args:
            shots: List of shots taken by the player
            
        Returns:
            Shooting analysis results
        """
        if not shots:
            return {
                'total_shots': 0,
                'field_goals_made': 0,
                'field_goal_percentage': 0,
                'three_pointers_attempted': 0,
                'three_pointers_made': 0,
                'three_point_percentage': 0,
                'two_pointers_attempted': 0,
                'two_pointers_made': 0,
                'two_point_percentage': 0,
                'points': 0,
                'shot_zones': {}
            }
        
        # Count shots and makes
        total_shots = len(shots)
        field_goals_made = sum(1 for shot in shots if shot.get('is_made', False))
        
        # Three-pointers
        three_pointers = [shot for shot in shots if shot.get('value', 2) == 3]
        three_pointers_attempted = len(three_pointers)
        three_pointers_made = sum(1 for shot in three_pointers if shot.get('is_made', False))
        
        # Two-pointers
        two_pointers = [shot for shot in shots if shot.get('value', 2) == 2]
        two_pointers_attempted = len(two_pointers)
        two_pointers_made = sum(1 for shot in two_pointers if shot.get('is_made', False))
        
        # Calculate percentages
        field_goal_percentage = (field_goals_made / total_shots) * 100 if total_shots > 0 else 0
        three_point_percentage = (three_pointers_made / three_pointers_attempted) * 100 if three_pointers_attempted > 0 else 0
        two_point_percentage = (two_pointers_made / two_pointers_attempted) * 100 if two_pointers_attempted > 0 else 0
        
        # Calculate points
        points = (three_pointers_made * 3) + (two_pointers_made * 2)
        
        # Analyze by zone
        zone_stats = {}
        for shot in shots:
            zone = shot.get('shot_zone', 'Unknown')
            if zone not in zone_stats:
                zone_stats[zone] = {
                    'attempts': 0,
                    'makes': 0,
                    'percentage': 0
                }
            
            zone_stats[zone]['attempts'] += 1
            if shot.get('is_made', False):
                zone_stats[zone]['makes'] += 1
        
        # Calculate percentages for each zone
        for zone, stats in zone_stats.items():
            stats['percentage'] = (stats['makes'] / stats['attempts']) * 100 if stats['attempts'] > 0 else 0
        
        return {
            'total_shots': total_shots,
            'field_goals_made': field_goals_made,
            'field_goal_percentage': field_goal_percentage,
            'three_pointers_attempted': three_pointers_attempted,
            'three_pointers_made': three_pointers_made,
            'three_point_percentage': three_point_percentage,
            'two_pointers_attempted': two_pointers_attempted,
            'two_pointers_made': two_pointers_made,
            'two_point_percentage': two_point_percentage,
            'points': points,
            'shot_zones': zone_stats
        }
    
    def _analyze_offensive_tendencies(self, player_data: Dict[str, Any], shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze offensive tendencies.
        
        Args:
            player_data: Player tracking and identification data
            shots: List of shots taken by the player
            
        Returns:
            Offensive tendencies analysis
        """
        # In a real implementation, we would analyze:
        # - Shot selection (mid-range vs. three-point vs. paint)
        # - Driving tendencies
        # - Pick and roll behavior
        # - Isolation tendencies
        # - Passing tendencies
        
        # For now, generate simulated tendencies
        shot_selection = {}
        if shots:
            # Count shots by zone
            zone_counts = {}
            for shot in shots:
                zone = shot.get('shot_zone', 'Unknown')
                zone_counts[zone] = zone_counts.get(zone, 0) + 1
            
            # Convert to percentages
            total_shots = len(shots)
            for zone, count in zone_counts.items():
                shot_selection[zone] = (count / total_shots) * 100
        
        return {
            'shot_selection': shot_selection,
            'driving_frequency': np.random.randint(1, 10),
            'pick_and_roll_frequency': np.random.randint(1, 10),
            'isolation_frequency': np.random.randint(1, 10),
            'post_up_frequency': np.random.randint(1, 10),
            'passing_rating': np.random.randint(1, 10),
            'ball_handling_rating': np.random.randint(1, 10),
            'off_ball_movement_rating': np.random.randint(1, 10)
        }
    
    def _analyze_defensive_tendencies(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze defensive tendencies.
        
        Args:
            player_data: Player tracking and identification data
            
        Returns:
            Defensive tendencies analysis
        """
        # In a real implementation, we would analyze:
        # - On-ball defense
        # - Help defense
        # - Rebounding
        # - Steals and blocks
        # - Pick and roll defense
        
        # For now, generate simulated tendencies
        return {
            'on_ball_defense_rating': np.random.randint(1, 10),
            'help_defense_rating': np.random.randint(1, 10),
            'rebounding_rating': np.random.randint(1, 10),
            'steals_rating': np.random.randint(1, 10),
            'blocks_rating': np.random.randint(1, 10),
            'pick_and_roll_defense': np.random.randint(1, 10),
            'closeout_rating': np.random.randint(1, 10)
        }
    
    def _analyze_physical_attributes(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze physical attributes.
        
        Args:
            player_data: Player tracking and identification data
            
        Returns:
            Physical attributes analysis
        """
        # In a real implementation, we would analyze:
        # - Speed
        # - Acceleration
        # - Vertical leap
        # - Strength
        # - Agility
        
        # For now, generate simulated attributes
        return {
            'speed': np.random.randint(1, 10),
            'acceleration': np.random.randint(1, 10),
            'vertical': np.random.randint(1, 10),
            'strength': np.random.randint(1, 10),
            'agility': np.random.randint(1, 10),
            'endurance': np.random.randint(1, 10)
        }
