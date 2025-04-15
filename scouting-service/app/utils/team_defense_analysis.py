"""
Team defense analysis module for basketball scouting.

This module provides functionality for analyzing team defensive patterns,
identifying defensive schemes, and evaluating defensive effectiveness.
"""
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
import math
import logging
from sklearn.cluster import KMeans
from app.utils.pose_estimation import PoseEstimator

# Initialize pose estimator
# Try to use YOLOv8 if available, otherwise fall back to MediaPipe
try:
    from ultralytics import YOLO
    pose_estimator = PoseEstimator(model_type="yolov8")
    print("Using YOLOv8 for team defense analysis")
except ImportError:
    pose_estimator = PoseEstimator(model_type="mediapipe")
    print("YOLOv8 not available, using MediaPipe for team defense analysis")

logger = logging.getLogger(__name__)

class TeamDefenseAnalyzer:
    """
    Team defense analysis for basketball scouting.
    """

    def __init__(self):
        """
        Initialize the team defense analyzer.
        """
        pass

    def analyze_team_defense(self, frames_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze team defense across multiple frames.

        Args:
            frames_data: List of frame data with player detections and poses

        Returns:
            Team defense analysis results
        """
        if not frames_data:
            return self._create_empty_analysis()

        try:
            # Extract defensive formations from each frame
            formations = []
            matchups = []
            defensive_stances = []
            defensive_movements = []
            defensive_rotations = []

            # Track players across frames for movement analysis
            player_keypoints_sequences = {}

            for frame_idx, frame_data in enumerate(frames_data):
                # Separate players into offensive and defensive teams
                # In a real implementation, this would use jersey colors or team assignments
                all_players = frame_data.get('players', [])
                if len(all_players) < 5:  # Need at least a few players for meaningful analysis
                    continue

                # Use team field if available, otherwise use simplified approach
                defensive_players = [p for p in all_players if p.get('team') == 'defense']
                offensive_players = [p for p in all_players if p.get('team') == 'offense']

                # Fallback to simplified team assignment if team field is not used
                if not defensive_players or not offensive_players:
                    mid_point = len(all_players) // 2
                    defensive_players = all_players[:mid_point]
                    offensive_players = all_players[mid_point:]

                # Analyze defensive formation
                if len(defensive_players) >= 3:  # Need at least 3 players for formation analysis
                    formation = pose_estimator.analyze_team_defensive_formation(defensive_players)
                    formations.append(formation)

                # Analyze defensive matchups
                if defensive_players and offensive_players:
                    frame_matchups = self._analyze_frame_matchups(defensive_players, offensive_players)
                    matchups.extend(frame_matchups)

                # Collect defensive stance data
                for player in defensive_players:
                    if 'keypoints' in player:
                        # Analyze stance
                        stance = pose_estimator.analyze_defensive_stance(player['keypoints'])
                        if stance:
                            defensive_stances.append({
                                'player_id': player.get('id', 0),
                                'stance': stance
                            })

                        # Track player keypoints for movement analysis
                        player_id = player.get('id', 0)
                        if player_id not in player_keypoints_sequences:
                            player_keypoints_sequences[player_id] = []
                        player_keypoints_sequences[player_id].append(player['keypoints'])

                # Analyze defensive rotations between consecutive frames
                if frame_idx > 0 and frame_idx < len(frames_data) - 1:
                    prev_frame = frames_data[frame_idx - 1]
                    prev_defensive_players = [p for p in prev_frame.get('players', []) if p.get('team') == 'defense']
                    if not prev_defensive_players:
                        mid_point = len(prev_frame.get('players', [])) // 2
                        prev_defensive_players = prev_frame.get('players', [])[:mid_point]

                    rotation_analysis = self._analyze_defensive_rotations(
                        prev_defensive_players, defensive_players, offensive_players
                    )
                    defensive_rotations.append(rotation_analysis)

            # Analyze player movements over time
            for player_id, keypoints_sequence in player_keypoints_sequences.items():
                if len(keypoints_sequence) > 1:  # Need at least 2 frames for movement analysis
                    movement_analysis = pose_estimator.analyze_defensive_movement(keypoints_sequence)
                    defensive_movements.append({
                        'player_id': player_id,
                        'movement': movement_analysis
                    })

            # Analyze defensive formations over time
            formation_analysis = self._analyze_formations(formations)

            # Analyze defensive matchups
            matchup_analysis = self._analyze_matchups(matchups)

            # Analyze defensive stances
            stance_analysis = self._analyze_stances(defensive_stances)

            # Analyze defensive movements
            movement_analysis = self._analyze_movements(defensive_movements)

            # Analyze defensive rotations
            rotation_analysis = self._analyze_rotations(defensive_rotations)

            # Identify defense type
            defense_type_analysis = self.identify_defense_type(formations)

            # Combine analyses into overall team defense analysis
            return {
                'formation_analysis': formation_analysis,
                'matchup_analysis': matchup_analysis,
                'stance_analysis': stance_analysis,
                'movement_analysis': movement_analysis,
                'rotation_analysis': rotation_analysis,
                'defense_type_analysis': defense_type_analysis,
                'overall_rating': self._calculate_overall_rating(
                    formation_analysis, matchup_analysis, stance_analysis,
                    movement_analysis, rotation_analysis, defense_type_analysis
                )
            }
        except Exception as e:
            logger.error(f"Error in team defense analysis: {e}")
            return self._create_empty_analysis()

    def _create_empty_analysis(self) -> Dict[str, Any]:
        """
        Create an empty analysis result.

        Returns:
            Empty analysis dictionary
        """
        return {
            'formation_analysis': {
                'primary_formation': 'Unknown',
                'formation_consistency': 0,
                'spacing_rating': 0,
                'pressure_rating': 0
            },
            'matchup_analysis': {
                'matchup_quality': 0,
                'best_defender_id': None,
                'weakest_defender_id': None
            },
            'stance_analysis': {
                'average_stance_quality': 0,
                'best_stance_player_id': None,
                'weakest_stance_player_id': None
            },
            'movement_analysis': {
                'average_movement_quality': 0,
                'best_movement_player_id': None,
                'weakest_movement_player_id': None
            },
            'rotation_analysis': {
                'rotation_quality': 0,
                'rotation_speed': 0,
                'help_defense_rating': 0
            },
            'defense_type_analysis': {
                'primary_defense': 'Unknown',
                'confidence': 0,
                'subtypes': {}
            },
            'defensive_matchups': [],
            'defensive_movements': [],
            'defensive_rotations': [],
            'overall_rating': 0
        }

    def _analyze_formations(self, formations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze defensive formations over time.

        Args:
            formations: List of formation analyses from different frames

        Returns:
            Formation analysis results
        """
        if not formations:
            return {
                'primary_formation': 'Unknown',
                'formation_consistency': 0,
                'spacing_rating': 0,
                'pressure_rating': 0
            }

        # Count formation types
        formation_types = {}
        for formation in formations:
            formation_type = formation.get('formation_type', 'Unknown')
            formation_types[formation_type] = formation_types.get(formation_type, 0) + 1

        # Determine primary formation
        primary_formation = max(formation_types.items(), key=lambda x: x[1])[0]

        # Calculate formation consistency (percentage of frames with primary formation)
        formation_consistency = (formation_types.get(primary_formation, 0) / len(formations)) * 10

        # Calculate average spacing and pressure ratings
        spacing_values = [f.get('spacing', 0) for f in formations]
        avg_spacing = sum(spacing_values) / len(spacing_values) if spacing_values else 0

        # Convert spacing to a 1-10 rating (lower spacing = higher rating)
        spacing_rating = max(1, min(10, int(10 - avg_spacing / 20)))

        # Count pressure levels
        pressure_counts = {'High': 0, 'Medium': 0, 'Low': 0}
        for formation in formations:
            pressure = formation.get('pressure_level', 'Low')
            pressure_counts[pressure] = pressure_counts.get(pressure, 0) + 1

        # Calculate pressure rating
        pressure_rating = (
            pressure_counts.get('High', 0) * 10 +
            pressure_counts.get('Medium', 0) * 6 +
            pressure_counts.get('Low', 0) * 3
        ) / len(formations)

        return {
            'primary_formation': primary_formation,
            'formation_consistency': round(formation_consistency, 1),
            'spacing_rating': spacing_rating,
            'pressure_rating': round(pressure_rating, 1),
            'formation_types': formation_types
        }

    def _analyze_matchups(self, matchups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze defensive matchups.

        Args:
            matchups: List of matchup analyses

        Returns:
            Matchup analysis results
        """
        if not matchups:
            return {
                'matchup_quality': 0,
                'best_defender_id': None,
                'weakest_defender_id': None
            }

        # Calculate average matchup quality
        matchup_qualities = [m.get('matchup_quality', 0) for m in matchups]
        avg_matchup_quality = sum(matchup_qualities) / len(matchup_qualities) if matchup_qualities else 0

        # Group matchups by defender
        defender_matchups = {}
        for matchup in matchups:
            defender_id = matchup.get('defensive_player_id')
            if defender_id is not None:
                if defender_id not in defender_matchups:
                    defender_matchups[defender_id] = []
                defender_matchups[defender_id].append(matchup.get('matchup_quality', 0))

        # Calculate average matchup quality for each defender
        defender_qualities = {}
        for defender_id, qualities in defender_matchups.items():
            defender_qualities[defender_id] = sum(qualities) / len(qualities) if qualities else 0

        # Find best and weakest defenders
        best_defender_id = None
        weakest_defender_id = None
        best_quality = 0
        weakest_quality = 10

        for defender_id, quality in defender_qualities.items():
            if quality > best_quality:
                best_quality = quality
                best_defender_id = defender_id
            if quality < weakest_quality:
                weakest_quality = quality
                weakest_defender_id = defender_id

        return {
            'matchup_quality': round(avg_matchup_quality, 1),
            'best_defender_id': best_defender_id,
            'best_defender_quality': round(best_quality, 1) if best_defender_id else 0,
            'weakest_defender_id': weakest_defender_id,
            'weakest_defender_quality': round(weakest_quality, 1) if weakest_defender_id else 0,
            'defender_qualities': defender_qualities
        }

    def _analyze_stances(self, stances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze defensive stances.

        Args:
            stances: List of stance analyses

        Returns:
            Stance analysis results
        """
        if not stances:
            return {
                'average_stance_quality': 0,
                'best_stance_player_id': None,
                'weakest_stance_player_id': None
            }

        # Group stances by player
        player_stances = {}
        for stance_data in stances:
            player_id = stance_data.get('player_id')
            stance = stance_data.get('stance', {})
            stance_quality = stance.get('stance_quality', 0)

            if player_id is not None:
                if player_id not in player_stances:
                    player_stances[player_id] = []
                player_stances[player_id].append(stance_quality)

        # Calculate average stance quality for each player
        player_qualities = {}
        for player_id, qualities in player_stances.items():
            player_qualities[player_id] = sum(qualities) / len(qualities) if qualities else 0

        # Calculate overall average stance quality
        all_qualities = [q for qualities in player_stances.values() for q in qualities]
        avg_stance_quality = sum(all_qualities) / len(all_qualities) if all_qualities else 0

        # Find best and weakest stance players
        best_player_id = None
        weakest_player_id = None
        best_quality = 0
        weakest_quality = 10

        for player_id, quality in player_qualities.items():
            if quality > best_quality:
                best_quality = quality
                best_player_id = player_id
            if quality < weakest_quality:
                weakest_quality = quality
                weakest_player_id = player_id

        return {
            'average_stance_quality': round(avg_stance_quality, 1),
            'best_stance_player_id': best_player_id,
            'best_stance_quality': round(best_quality, 1) if best_player_id else 0,
            'weakest_stance_player_id': weakest_player_id,
            'weakest_stance_quality': round(weakest_quality, 1) if weakest_player_id else 0,
            'player_qualities': player_qualities
        }

    def _analyze_frame_matchups(self, defensive_players: List[Dict[str, Any]], offensive_players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze defensive matchups for a single frame.

        Args:
            defensive_players: List of defensive player detections with keypoints
            offensive_players: List of offensive player detections with keypoints

        Returns:
            List of matchup analyses
        """
        matchups = []

        # For each defensive player, find the closest offensive player
        for def_player in defensive_players:
            if 'keypoints' not in def_player:
                continue

            def_id = def_player.get('id', 0)
            def_position = self._get_player_position(def_player)

            closest_off_player = None
            min_distance = float('inf')

            for off_player in offensive_players:
                if 'keypoints' not in off_player:
                    continue

                # Get player position
                off_position = self._get_player_position(off_player)

                # Calculate distance between players
                distance = self._calculate_distance(def_position, off_position)

                if distance < min_distance:
                    min_distance = distance
                    closest_off_player = off_player

            if closest_off_player:
                # Calculate matchup quality (1-10 scale)
                # Lower distance = higher quality
                matchup_quality = max(1, min(10, int(10 - min_distance / 20)))

                # Add matchup analysis
                matchups.append({
                    'defensive_player_id': def_id,
                    'offensive_player_id': closest_off_player.get('id', 0),
                    'distance': min_distance,
                    'matchup_quality': matchup_quality
                })

        return matchups

    def _analyze_defensive_rotations(self, prev_defensive_players: List[Dict[str, Any]],
                                   curr_defensive_players: List[Dict[str, Any]],
                                   offensive_players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze defensive rotations between consecutive frames.

        Args:
            prev_defensive_players: Defensive players from previous frame
            curr_defensive_players: Defensive players from current frame
            offensive_players: Offensive players from current frame

        Returns:
            Rotation analysis results
        """
        # Map players between frames by ID
        prev_players_map = {p.get('id', 0): p for p in prev_defensive_players if 'keypoints' in p}
        curr_players_map = {p.get('id', 0): p for p in curr_defensive_players if 'keypoints' in p}

        # Find common player IDs between frames
        common_ids = set(prev_players_map.keys()) & set(curr_players_map.keys())

        if not common_ids:
            return {
                'rotation_quality': 0,
                'rotation_speed': 0,
                'help_defense_rating': 0
            }

        # Calculate rotation metrics
        rotation_speeds = []
        help_defense_scores = []

        for player_id in common_ids:
            prev_player = prev_players_map[player_id]
            curr_player = curr_players_map[player_id]

            # Calculate player movement between frames
            prev_pos = self._get_player_position(prev_player)
            curr_pos = self._get_player_position(curr_player)
            movement_distance = self._calculate_distance(prev_pos, curr_pos)

            # Calculate rotation speed
            rotation_speeds.append(movement_distance)

            # Analyze help defense
            # Find if player moved closer to an offensive player they weren't guarding
            prev_matchups = self._analyze_frame_matchups([prev_player], offensive_players)
            curr_matchups = self._analyze_frame_matchups([curr_player], offensive_players)

            if prev_matchups and curr_matchups:
                prev_guarded_id = prev_matchups[0].get('offensive_player_id')
                curr_guarded_id = curr_matchups[0].get('offensive_player_id')

                # If guarding different players, might be help defense
                if prev_guarded_id != curr_guarded_id:
                    help_defense_scores.append(8)  # Good help defense score
                else:
                    help_defense_scores.append(5)  # Neutral score

        # Calculate average rotation speed and help defense rating
        avg_rotation_speed = sum(rotation_speeds) / len(rotation_speeds) if rotation_speeds else 0
        avg_help_defense = sum(help_defense_scores) / len(help_defense_scores) if help_defense_scores else 0

        # Calculate overall rotation quality
        rotation_quality = (avg_rotation_speed * 0.5 + avg_help_defense * 0.5)
        rotation_quality = max(1, min(10, rotation_quality))

        return {
            'rotation_quality': round(rotation_quality, 1),
            'rotation_speed': round(avg_rotation_speed, 1),
            'help_defense_rating': round(avg_help_defense, 1)
        }

    def _analyze_movements(self, movements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze defensive movements.

        Args:
            movements: List of movement analyses

        Returns:
            Movement analysis results
        """
        if not movements:
            return {
                'average_movement_quality': 0,
                'best_movement_player_id': None,
                'weakest_movement_player_id': None
            }

        # Extract movement qualities
        player_qualities = {}
        for movement_data in movements:
            player_id = movement_data.get('player_id')
            movement = movement_data.get('movement', {})
            movement_quality = movement.get('movement_quality', 0)

            if player_id is not None:
                player_qualities[player_id] = movement_quality

        # Calculate average movement quality
        avg_movement_quality = sum(player_qualities.values()) / len(player_qualities) if player_qualities else 0

        # Find best and weakest movement players
        best_player_id = None
        weakest_player_id = None
        best_quality = 0
        weakest_quality = 10

        for player_id, quality in player_qualities.items():
            if quality > best_quality:
                best_quality = quality
                best_player_id = player_id
            if quality < weakest_quality:
                weakest_quality = quality
                weakest_player_id = player_id

        return {
            'average_movement_quality': round(avg_movement_quality, 1),
            'best_movement_player_id': best_player_id,
            'best_movement_quality': round(best_quality, 1) if best_player_id else 0,
            'weakest_movement_player_id': weakest_player_id,
            'weakest_movement_quality': round(weakest_quality, 1) if weakest_player_id else 0,
            'player_qualities': player_qualities
        }

    def _analyze_rotations(self, rotations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze defensive rotations.

        Args:
            rotations: List of rotation analyses

        Returns:
            Rotation analysis results
        """
        if not rotations:
            return {
                'rotation_quality': 0,
                'rotation_speed': 0,
                'help_defense_rating': 0
            }

        # Calculate average rotation metrics
        rotation_qualities = [r.get('rotation_quality', 0) for r in rotations]
        rotation_speeds = [r.get('rotation_speed', 0) for r in rotations]
        help_defense_ratings = [r.get('help_defense_rating', 0) for r in rotations]

        avg_rotation_quality = sum(rotation_qualities) / len(rotation_qualities) if rotation_qualities else 0
        avg_rotation_speed = sum(rotation_speeds) / len(rotation_speeds) if rotation_speeds else 0
        avg_help_defense = sum(help_defense_ratings) / len(help_defense_ratings) if help_defense_ratings else 0

        return {
            'rotation_quality': round(avg_rotation_quality, 1),
            'rotation_speed': round(avg_rotation_speed, 1),
            'help_defense_rating': round(avg_help_defense, 1)
        }

    def _get_player_position(self, player: Dict[str, Any]) -> List[float]:
        """
        Get player position from keypoints.

        Args:
            player: Player detection with keypoints

        Returns:
            Player position as [x, y]
        """
        if 'keypoints' in player:
            keypoints = player['keypoints']
            try:
                # Use hip center as player position
                right_hip_idx = 8  # Assuming right_hip is at index 8
                left_hip_idx = 11  # Assuming left_hip is at index 11
                right_hip = keypoints[right_hip_idx][:2]
                left_hip = keypoints[left_hip_idx][:2]
                return [(right_hip[0] + left_hip[0]) / 2, (right_hip[1] + left_hip[1]) / 2]
            except (IndexError, KeyError):
                pass

        # Fallback to bounding box center
        if 'bbox' in player:
            x1, y1, x2, y2 = player['bbox']
            return [(x1 + x2) / 2, (y1 + y2) / 2]

        # Default position if all else fails
        return [0, 0]

    def _calculate_distance(self, pos1: List[float], pos2: List[float]) -> float:
        """
        Calculate Euclidean distance between two positions.

        Args:
            pos1: First position [x, y]
            pos2: Second position [x, y]

        Returns:
            Euclidean distance
        """
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    def _calculate_overall_rating(
        self,
        formation_analysis: Dict[str, Any],
        matchup_analysis: Dict[str, Any],
        stance_analysis: Dict[str, Any],
        movement_analysis: Dict[str, Any],
        rotation_analysis: Dict[str, Any],
        defense_type_analysis: Dict[str, Any] = None
    ) -> float:
        """
        Calculate overall team defense rating.

        Args:
            formation_analysis: Formation analysis results
            matchup_analysis: Matchup analysis results
            stance_analysis: Stance analysis results
            movement_analysis: Movement analysis results
            rotation_analysis: Rotation analysis results

        Returns:
            Overall team defense rating (1-10)
        """
        # Weight the different components
        formation_weight = 0.25
        matchup_weight = 0.2
        stance_weight = 0.15
        movement_weight = 0.2
        rotation_weight = 0.2

        # Extract ratings
        formation_rating = (
            formation_analysis.get('formation_consistency', 0) * 0.4 +
            formation_analysis.get('spacing_rating', 0) * 0.3 +
            formation_analysis.get('pressure_rating', 0) * 0.3
        )

        matchup_rating = matchup_analysis.get('matchup_quality', 0)
        stance_rating = stance_analysis.get('average_stance_quality', 0)
        movement_rating = movement_analysis.get('average_movement_quality', 0)
        rotation_rating = rotation_analysis.get('rotation_quality', 0)

        # Calculate weighted average
        overall_rating = (
            formation_rating * formation_weight +
            matchup_rating * matchup_weight +
            stance_rating * stance_weight +
            movement_rating * movement_weight +
            rotation_rating * rotation_weight
        )

        # Add bonus for consistent defense type
        if defense_type_analysis:
            defense_confidence = defense_type_analysis.get('confidence', 0) / 100  # Convert to 0-1 scale

            # Add up to 1 point bonus for consistent defense
            consistency_bonus = defense_confidence
            overall_rating += consistency_bonus

        # Ensure rating is in 1-10 range
        return round(max(1, min(10, overall_rating)), 1)

    def identify_defense_type(self, formations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify the type of defense being played.

        Args:
            formations: List of formation analyses from different frames

        Returns:
            Defense type analysis
        """
        if not formations:
            return {
                'primary_defense': 'Unknown',
                'confidence': 0,
                'subtypes': {}
            }

        # Count formation types
        defense_types = {}
        for formation in formations:
            defense_type = formation.get('formation_type', 'Unknown')
            defense_types[defense_type] = defense_types.get(defense_type, 0) + 1

        # Determine primary defense type
        primary_defense = max(defense_types.items(), key=lambda x: x[1])[0]

        # Calculate confidence (percentage of frames with primary defense)
        confidence = (defense_types.get(primary_defense, 0) / len(formations)) * 100

        # Analyze subtypes based on primary defense
        subtypes = {}
        if primary_defense == 'Man-to-Man':
            # Analyze man-to-man subtypes (switching, hedging, etc.)
            subtypes = self._analyze_man_defense_subtypes(formations)
        elif 'Zone' in primary_defense:
            # Zone defense is already classified by formation type
            subtypes = {primary_defense: confidence}
        else:
            # Mixed or unknown defense
            subtypes = defense_types

        return {
            'primary_defense': primary_defense,
            'confidence': round(confidence, 1),
            'subtypes': subtypes
        }

    def _analyze_man_defense_subtypes(self, formations: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Analyze man-to-man defense subtypes.

        Args:
            formations: List of formation analyses from different frames

        Returns:
            Dictionary of man-to-man subtypes with confidence values
        """
        if not formations:
            return {
                'Regular Man-to-Man': 100.0
            }

        # Count player positions to detect switching and hedging
        player_position_changes = 0
        player_clusters = 0
        player_spacing = 0

        for i in range(1, len(formations)):
            prev_formation = formations[i-1]
            curr_formation = formations[i]

            # Check for player position changes
            prev_positions = prev_formation.get('player_positions', [])
            curr_positions = curr_formation.get('player_positions', [])

            if prev_positions and curr_positions:
                # Count position changes as a proxy for switching
                player_position_changes += 1

            # Check for clustering as a proxy for hedging/helping
            if 'clusters' in curr_formation:
                clusters = curr_formation['clusters']
                if 'counts' in clusters:
                    # If any cluster has more than 1 player, might be hedging/helping
                    counts = clusters.get('counts', [])
                    if any(count > 1 for count in counts):
                        player_clusters += 1

            # Check spacing as a proxy for help defense
            spacing = curr_formation.get('spacing', 0)
            if spacing < 50:  # Close spacing indicates help defense
                player_spacing += 1

        # Calculate percentages
        total_frames = len(formations)
        switching_pct = (player_position_changes / total_frames) * 100 if total_frames > 0 else 0
        hedging_pct = (player_clusters / total_frames) * 100 if total_frames > 0 else 0
        helping_pct = (player_spacing / total_frames) * 100 if total_frames > 0 else 0

        # Regular man-to-man is the remainder
        regular_pct = max(0, 100 - switching_pct - hedging_pct - helping_pct)

        return {
            'Regular Man-to-Man': round(regular_pct, 1),
            'Switching': round(switching_pct, 1),
            'Hedging': round(hedging_pct, 1),
            'Help Defense': round(helping_pct, 1)
        }


# Create a singleton instance
team_defense_analyzer = TeamDefenseAnalyzer()
