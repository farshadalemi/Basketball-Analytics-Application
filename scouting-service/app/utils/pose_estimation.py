"""
Pose estimation module for basketball player analysis.

This module provides functionality for detecting and analyzing player poses
in basketball videos, which is essential for defensive analysis.
It includes capabilities for analyzing individual defensive stances and team defensive formations.
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
import os
import math
from pathlib import Path
from scipy.spatial import distance
from sklearn.cluster import KMeans
import logging

logger = logging.getLogger(__name__)

class PoseEstimator:
    """
    Human pose estimation using MediaPipe, YOLOv8, or OpenPose.
    """

    def __init__(self, model_type: str = "mediapipe"):
        """
        Initialize the pose estimator.

        Args:
            model_type: Type of pose estimation model to use ("mediapipe", "yolov8", or "openpose")
        """
        self.model_type = model_type
        self.model = self._initialize_model()

        # Define keypoint indices for different body parts
        self.keypoint_indices = {
            "nose": 0,
            "neck": 1,
            "right_shoulder": 2,
            "right_elbow": 3,
            "right_wrist": 4,
            "left_shoulder": 5,
            "left_elbow": 6,
            "left_wrist": 7,
            "right_hip": 8,
            "right_knee": 9,
            "right_ankle": 10,
            "left_hip": 11,
            "left_knee": 12,
            "left_ankle": 13,
            "right_eye": 14,
            "left_eye": 15,
            "right_ear": 16,
            "left_ear": 17
        }

    def _initialize_model(self) -> Any:
        """
        Initialize the pose estimation model.

        Returns:
            Initialized pose estimation model
        """
        if self.model_type == "mediapipe":
            try:
                import mediapipe as mp
                mp_pose = mp.solutions.pose
                model = mp_pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,  # 0=Lite, 1=Full, 2=Heavy
                    smooth_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                print("Initialized MediaPipe Pose model")
                return model
            except ImportError:
                print("Warning: mediapipe not installed. Using fallback pose estimation.")
                return None
        elif self.model_type == "yolov8":
            try:
                from ultralytics import YOLO
                # Load YOLOv8 pose estimation model
                model = YOLO('yolov8n-pose.pt')
                print("Initialized YOLOv8 Pose model")
                return model
            except ImportError:
                print("Warning: ultralytics not installed. Using fallback pose estimation.")
                return None
        elif self.model_type == "openpose":
            try:
                # Check if OpenPose Python API is available
                # This is a placeholder as OpenPose integration depends on the specific installation
                # and might require custom implementation
                print("OpenPose integration requires custom implementation")
                return "OpenPose Placeholder"
            except Exception:
                print("Warning: OpenPose not available. Using fallback pose estimation.")
                return None
        else:
            print(f"Unknown model type: {self.model_type}. Using fallback pose estimation.")
            return None

    def detect_poses(self, frame: np.ndarray, player_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect poses for players in a frame.

        Args:
            frame: Video frame as numpy array
            player_detections: List of player detections with bounding boxes

        Returns:
            List of player detections with pose keypoints
        """
        poses = []

        # If we have a MediaPipe model, use it
        if self.model_type == "mediapipe" and self.model is not None:
            try:
                # Process each player detection
                for detection in player_detections:
                    # Extract player bounding box
                    bbox = detection['bbox']
                    x1, y1, x2, y2 = bbox

                    # Expand the bounding box slightly to ensure all body parts are included
                    height, width = frame.shape[:2]
                    x1 = max(0, x1 - 20)
                    y1 = max(0, y1 - 20)
                    x2 = min(width, x2 + 20)
                    y2 = min(height, y2 + 20)

                    # Extract player region
                    player_img = frame[y1:y2, x1:x2]
                    if player_img.size == 0:
                        continue

                    # Convert to RGB for MediaPipe
                    player_img_rgb = cv2.cvtColor(player_img, cv2.COLOR_BGR2RGB)

                    # Process the image
                    results = self.model.process(player_img_rgb)

                    # Extract pose landmarks
                    if results.pose_landmarks:
                        # Convert normalized landmarks to pixel coordinates
                        keypoints = []
                        for landmark in results.pose_landmarks.landmark:
                            # Convert normalized coordinates to pixel coordinates
                            px = int(landmark.x * player_img.shape[1]) + x1
                            py = int(landmark.y * player_img.shape[0]) + y1
                            confidence = landmark.visibility
                            keypoints.append([px, py, confidence])

                        # Add pose to detection
                        detection_with_pose = detection.copy()
                        detection_with_pose['keypoints'] = keypoints
                        poses.append(detection_with_pose)
                    else:
                        # If no pose detected, add the original detection
                        poses.append(detection)

                return poses
            except Exception as e:
                print(f"Error in MediaPipe pose detection: {e}")
                # Fall back to OpenCV-based pose estimation if MediaPipe fails

        # If we have a YOLOv8 model, use it
        elif self.model_type == "yolov8" and self.model is not None:
            try:
                # Process the entire frame with YOLOv8 pose estimation
                results = self.model(frame, verbose=False)

                # Map YOLOv8 keypoints to our keypoint format
                yolo_keypoint_map = {
                    0: "nose",
                    5: "left_shoulder",
                    6: "right_shoulder",
                    7: "left_elbow",
                    8: "right_elbow",
                    9: "left_wrist",
                    10: "right_wrist",
                    11: "left_hip",
                    12: "right_hip",
                    13: "left_knee",
                    14: "right_knee",
                    15: "left_ankle",
                    16: "right_ankle"
                }

                # Process each player detection
                for detection in player_detections:
                    bbox = detection['bbox']
                    x1, y1, x2, y2 = bbox

                    # Find the closest YOLOv8 detection to this bounding box
                    best_match = None
                    best_iou = 0

                    for result in results:
                        if hasattr(result, 'keypoints') and len(result.keypoints) > 0:
                            for i, keypoints in enumerate(result.keypoints):
                                if hasattr(result, 'boxes') and i < len(result.boxes):
                                    yolo_box = result.boxes[i].xyxy[0].tolist()  # [x1, y1, x2, y2]

                                    # Calculate IoU between detection bbox and YOLOv8 bbox
                                    iou = self._calculate_iou(bbox, yolo_box)

                                    if iou > best_iou and iou > 0.5:  # Threshold for matching
                                        best_iou = iou
                                        best_match = keypoints

                    if best_match is not None:
                        # Convert YOLOv8 keypoints to our format
                        keypoints = []

                        # Initialize with default values
                        for _ in range(18):  # We have 18 keypoints in our format
                            keypoints.append([0, 0, 0])  # [x, y, confidence]

                        # Fill in the keypoints we have from YOLOv8
                        for i, kp in enumerate(best_match):
                            if i in yolo_keypoint_map and kp is not None and len(kp) >= 3:
                                x, y, conf = kp.tolist()
                                idx = self.keypoint_indices[yolo_keypoint_map[i]]
                                keypoints[idx] = [float(x), float(y), float(conf)]

                        # Add neck keypoint (midpoint between shoulders)
                        left_shoulder_idx = self.keypoint_indices["left_shoulder"]
                        right_shoulder_idx = self.keypoint_indices["right_shoulder"]
                        if keypoints[left_shoulder_idx][2] > 0 and keypoints[right_shoulder_idx][2] > 0:
                            neck_x = (keypoints[left_shoulder_idx][0] + keypoints[right_shoulder_idx][0]) / 2
                            neck_y = (keypoints[left_shoulder_idx][1] + keypoints[right_shoulder_idx][1]) / 2
                            neck_conf = (keypoints[left_shoulder_idx][2] + keypoints[right_shoulder_idx][2]) / 2
                            keypoints[self.keypoint_indices["neck"]] = [neck_x, neck_y, neck_conf]

                        # Add pose to detection
                        detection_with_pose = detection.copy()
                        detection_with_pose['keypoints'] = keypoints
                        poses.append(detection_with_pose)
                    else:
                        # If no matching pose detected, add the original detection
                        poses.append(detection)

                return poses
            except Exception as e:
                logger.error(f"Error in YOLOv8 pose detection: {e}")
                # Fall back to simple pose estimation

        # If we have an OpenPose model, use it
        elif self.model_type == "openpose" and self.model is not None and self.model != "OpenPose Placeholder":
            try:
                # OpenPose implementation would go here
                # This is a placeholder as OpenPose integration depends on the specific installation
                print("OpenPose detection not implemented")
                return player_detections
            except Exception as e:
                print(f"Error in OpenPose detection: {e}")
                # Fall back to simple pose estimation

        # Fallback: Generate simple pose keypoints based on bounding box
        for detection in player_detections:
            bbox = detection['bbox']
            x1, y1, x2, y2 = bbox

            # Calculate basic body proportions
            width = x2 - x1
            height = y2 - y1

            # Generate simple keypoints based on typical human proportions
            # These are rough approximations and not accurate
            keypoints = [
                [x1 + width // 2, y1 + height // 8, 0.9],  # nose
                [x1 + width // 2, y1 + height // 4, 0.9],  # neck
                [x1 + width // 3, y1 + height // 3, 0.8],  # right_shoulder
                [x1 + width // 4, y1 + height // 2, 0.7],  # right_elbow
                [x1 + width // 5, y1 + 2 * height // 3, 0.6],  # right_wrist
                [x1 + 2 * width // 3, y1 + height // 3, 0.8],  # left_shoulder
                [x1 + 3 * width // 4, y1 + height // 2, 0.7],  # left_elbow
                [x1 + 4 * width // 5, y1 + 2 * height // 3, 0.6],  # left_wrist
                [x1 + width // 3, y1 + 2 * height // 3, 0.8],  # right_hip
                [x1 + width // 3, y1 + 5 * height // 6, 0.7],  # right_knee
                [x1 + width // 3, y1 + height, 0.6],  # right_ankle
                [x1 + 2 * width // 3, y1 + 2 * height // 3, 0.8],  # left_hip
                [x1 + 2 * width // 3, y1 + 5 * height // 6, 0.7],  # left_knee
                [x1 + 2 * width // 3, y1 + height, 0.6],  # left_ankle
                [x1 + width // 3, y1 + height // 10, 0.7],  # right_eye
                [x1 + 2 * width // 3, y1 + height // 10, 0.7],  # left_eye
                [x1 + width // 4, y1 + height // 8, 0.6],  # right_ear
                [x1 + 3 * width // 4, y1 + height // 8, 0.6]  # left_ear
            ]

            # Add pose to detection
            detection_with_pose = detection.copy()
            detection_with_pose['keypoints'] = keypoints
            poses.append(detection_with_pose)

        return poses

    def _calculate_iou(self, box1: List[float], box2: List[float]) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes.

        Args:
            box1: First bounding box [x1, y1, x2, y2]
            box2: Second bounding box [x1, y1, x2, y2]

        Returns:
            IoU value between 0 and 1
        """
        # Determine the coordinates of the intersection rectangle
        x_left = max(box1[0], box2[0])
        y_top = max(box1[1], box2[1])
        x_right = min(box1[2], box2[2])
        y_bottom = min(box1[3], box2[3])

        # If the boxes don't intersect, return 0
        if x_right < x_left or y_bottom < y_top:
            return 0.0

        # Calculate intersection area
        intersection_area = (x_right - x_left) * (y_bottom - y_top)

        # Calculate area of each box
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

        # Calculate union area
        union_area = box1_area + box2_area - intersection_area

        # Calculate IoU
        iou = intersection_area / union_area if union_area > 0 else 0.0

        return iou

    def analyze_defensive_stance(self, keypoints: List[List[float]]) -> Dict[str, Any]:
        """
        Analyze the defensive stance of a player based on pose keypoints.

        Args:
            keypoints: List of pose keypoints [x, y, confidence]

        Returns:
            Dictionary with defensive stance analysis
        """
        # Extract relevant keypoints
        try:
            nose = keypoints[self.keypoint_indices["nose"]][:2]
            right_shoulder = keypoints[self.keypoint_indices["right_shoulder"]][:2]
            left_shoulder = keypoints[self.keypoint_indices["left_shoulder"]][:2]
            right_hip = keypoints[self.keypoint_indices["right_hip"]][:2]
            left_hip = keypoints[self.keypoint_indices["left_hip"]][:2]
            right_knee = keypoints[self.keypoint_indices["right_knee"]][:2]
            left_knee = keypoints[self.keypoint_indices["left_knee"]][:2]
            right_ankle = keypoints[self.keypoint_indices["right_ankle"]][:2]
            left_ankle = keypoints[self.keypoint_indices["left_ankle"]][:2]

            # Calculate stance width (distance between ankles)
            stance_width = math.sqrt((right_ankle[0] - left_ankle[0])**2 + (right_ankle[1] - left_ankle[1])**2)

            # Calculate knee bend (vertical distance between hip and knee)
            right_knee_bend = right_hip[1] - right_knee[1]
            left_knee_bend = left_hip[1] - left_knee[1]
            knee_bend = (right_knee_bend + left_knee_bend) / 2

            # Calculate torso angle (angle between vertical and line from hip to shoulder)
            hip_center = [(right_hip[0] + left_hip[0]) / 2, (right_hip[1] + left_hip[1]) / 2]
            shoulder_center = [(right_shoulder[0] + left_shoulder[0]) / 2, (right_shoulder[1] + left_shoulder[1]) / 2]

            # Calculate angle (0 is vertical, positive is leaning forward)
            dx = shoulder_center[0] - hip_center[0]
            dy = hip_center[1] - shoulder_center[1]  # Inverted y-axis in image coordinates
            torso_angle = math.degrees(math.atan2(dx, dy))

            # Calculate arm extension (average distance from shoulder to wrist)
            right_elbow = keypoints[self.keypoint_indices["right_elbow"]][:2]
            left_elbow = keypoints[self.keypoint_indices["left_elbow"]][:2]
            right_wrist = keypoints[self.keypoint_indices["right_wrist"]][:2]
            left_wrist = keypoints[self.keypoint_indices["left_wrist"]][:2]

            right_arm_extension = math.sqrt((right_shoulder[0] - right_wrist[0])**2 + (right_shoulder[1] - right_wrist[1])**2)
            left_arm_extension = math.sqrt((left_shoulder[0] - left_wrist[0])**2 + (left_shoulder[1] - left_wrist[1])**2)
            arm_extension = (right_arm_extension + left_arm_extension) / 2

            # Analyze defensive stance quality
            # These thresholds would need to be calibrated based on actual data
            stance_quality = 0

            # Good defensive stance has wide feet, bent knees, and upright torso
            if stance_width > 50:  # Wide stance
                stance_quality += 3
            elif stance_width > 30:  # Medium stance
                stance_quality += 2
            else:  # Narrow stance
                stance_quality += 1

            if knee_bend < -20:  # Knees bent significantly
                stance_quality += 3
            elif knee_bend < -10:  # Knees bent moderately
                stance_quality += 2
            else:  # Knees straight
                stance_quality += 1

            if abs(torso_angle) < 15:  # Upright torso
                stance_quality += 3
            elif abs(torso_angle) < 30:  # Slightly leaning
                stance_quality += 2
            else:  # Significantly leaning
                stance_quality += 1

            if arm_extension > 100:  # Arms extended
                stance_quality += 3
            elif arm_extension > 70:  # Arms partially extended
                stance_quality += 2
            else:  # Arms not extended
                stance_quality += 1

            # Normalize to 1-10 scale
            stance_quality = min(10, max(1, int(stance_quality * 10 / 12)))

            return {
                "stance_width": stance_width,
                "knee_bend": knee_bend,
                "torso_angle": torso_angle,
                "arm_extension": arm_extension,
                "stance_quality": stance_quality,
                "is_defensive_stance": stance_quality >= 7
            }
        except (IndexError, TypeError) as e:
            print(f"Error analyzing defensive stance: {e}")
            return {
                "stance_width": 0,
                "knee_bend": 0,
                "torso_angle": 0,
                "arm_extension": 0,
                "stance_quality": 1,
                "is_defensive_stance": False
            }

    def analyze_defensive_movement(self, keypoints_sequence: List[List[List[float]]]) -> Dict[str, Any]:
        """
        Analyze the defensive movement of a player over a sequence of frames.

        Args:
            keypoints_sequence: List of pose keypoints for each frame

        Returns:
            Dictionary with defensive movement analysis
        """
        if not keypoints_sequence or len(keypoints_sequence) < 2:
            return {
                "lateral_movement": 0,
                "vertical_movement": 0,
                "movement_speed": 0,
                "direction_changes": 0,
                "movement_quality": 1
            }

        try:
            # Track hip center movement as proxy for player movement
            hip_centers = []
            for keypoints in keypoints_sequence:
                right_hip = keypoints[self.keypoint_indices["right_hip"]][:2]
                left_hip = keypoints[self.keypoint_indices["left_hip"]][:2]
                hip_center = [(right_hip[0] + left_hip[0]) / 2, (right_hip[1] + left_hip[1]) / 2]
                hip_centers.append(hip_center)

            # Calculate movement metrics
            lateral_movements = []
            vertical_movements = []

            for i in range(1, len(hip_centers)):
                lateral_movements.append(hip_centers[i][0] - hip_centers[i-1][0])
                vertical_movements.append(hip_centers[i][1] - hip_centers[i-1][1])

            # Calculate total lateral and vertical movement
            total_lateral = sum(abs(m) for m in lateral_movements)
            total_vertical = sum(abs(m) for m in vertical_movements)

            # Calculate average movement speed
            total_movement = math.sqrt(total_lateral**2 + total_vertical**2)
            avg_speed = total_movement / len(keypoints_sequence)

            # Count direction changes (sign changes in movement)
            direction_changes = 0
            for i in range(1, len(lateral_movements)):
                if (lateral_movements[i] > 0 and lateral_movements[i-1] < 0) or \
                   (lateral_movements[i] < 0 and lateral_movements[i-1] > 0):
                    direction_changes += 1

            # Analyze movement quality
            # Good defensive movement has more lateral than vertical movement
            # and appropriate direction changes
            movement_quality = 0

            # More lateral than vertical movement is good for defense
            lateral_ratio = total_lateral / (total_vertical + 1e-5)  # Avoid division by zero
            if lateral_ratio > 2:  # Much more lateral than vertical
                movement_quality += 4
            elif lateral_ratio > 1:  # More lateral than vertical
                movement_quality += 3
            elif lateral_ratio > 0.5:  # Similar lateral and vertical
                movement_quality += 2
            else:  # More vertical than lateral
                movement_quality += 1

            # Some direction changes are good, but too many might indicate inefficiency
            if 1 <= direction_changes <= 3:  # Optimal range
                movement_quality += 3
            elif direction_changes > 3:  # Too many changes
                movement_quality += 2
            else:  # Too few changes
                movement_quality += 1

            # Normalize to 1-10 scale
            movement_quality = min(10, max(1, int(movement_quality * 10 / 7)))

            return {
                "lateral_movement": total_lateral,
                "vertical_movement": total_vertical,
                "movement_speed": avg_speed,
                "direction_changes": direction_changes,
                "movement_quality": movement_quality
            }
        except (IndexError, TypeError) as e:
            print(f"Error analyzing defensive movement: {e}")
            return {
                "lateral_movement": 0,
                "vertical_movement": 0,
                "movement_speed": 0,
                "direction_changes": 0,
                "movement_quality": 1
            }


    def analyze_team_defensive_formation(self, player_poses: List[Dict[str, Any]], court_dimensions: Tuple[int, int] = (94, 50)) -> Dict[str, Any]:
        """
        Analyze the team defensive formation based on the poses of all players.

        Args:
            player_poses: List of player detections with pose keypoints
            court_dimensions: Basketball court dimensions in feet (length, width)

        Returns:
            Dictionary with team defensive formation analysis
        """
        if not player_poses or len(player_poses) < 3:  # Need at least 3 players for meaningful formation analysis
            return {
                "formation_type": "Unknown",
                "spacing": 0,
                "defensive_line": "Unknown",
                "pressure_level": "Low",
                "formation_quality": 1
            }

        try:
            # Extract player positions (use hip center as player position)
            player_positions = []
            for player in player_poses:
                if 'keypoints' in player:
                    keypoints = player['keypoints']
                    try:
                        right_hip = keypoints[self.keypoint_indices["right_hip"]][:2]
                        left_hip = keypoints[self.keypoint_indices["left_hip"]][:2]
                        hip_center = [(right_hip[0] + left_hip[0]) / 2, (right_hip[1] + left_hip[1]) / 2]
                        player_positions.append({
                            'position': hip_center,
                            'player_id': player.get('id', 0),
                            'stance_quality': self.analyze_defensive_stance(keypoints).get('stance_quality', 0)
                        })
                    except (IndexError, KeyError):
                        # If hip keypoints are not available, use the center of the bounding box
                        if 'bbox' in player:
                            x1, y1, x2, y2 = player['bbox']
                            center = [(x1 + x2) / 2, (y1 + y2) / 2]
                            player_positions.append({
                                'position': center,
                                'player_id': player.get('id', 0),
                                'stance_quality': 0
                            })

            if not player_positions:
                return {
                    "formation_type": "Unknown",
                    "spacing": 0,
                    "defensive_line": "Unknown",
                    "pressure_level": "Low",
                    "formation_quality": 1
                }

            # Calculate team spacing (average distance between players)
            distances = []
            for i in range(len(player_positions)):
                for j in range(i+1, len(player_positions)):
                    pos1 = player_positions[i]['position']
                    pos2 = player_positions[j]['position']
                    dist = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                    distances.append(dist)

            avg_spacing = sum(distances) / len(distances) if distances else 0

            # Determine formation type based on player positions
            # This is a simplified approach and would need to be refined with actual game data
            positions_array = np.array([p['position'] for p in player_positions])

            # Use K-means to identify clusters in the defensive formation
            n_clusters = min(3, len(positions_array))
            kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(positions_array)
            cluster_centers = kmeans.cluster_centers_
            cluster_labels = kmeans.labels_

            # Count players in each cluster
            cluster_counts = np.bincount(cluster_labels, minlength=n_clusters)

            # Determine formation type based on cluster distribution
            if n_clusters == 1 or max(cluster_counts) >= len(player_positions) - 1:
                formation_type = "Man-to-Man"
            elif n_clusters == 2:
                if abs(cluster_counts[0] - cluster_counts[1]) <= 1:  # Roughly equal distribution
                    formation_type = "2-3 Zone"
                else:
                    formation_type = "1-3-1 Zone"
            elif n_clusters == 3:
                if max(cluster_counts) <= 2:  # No cluster has more than 2 players
                    formation_type = "3-2 Zone"
                else:
                    formation_type = "1-2-2 Zone"
            else:
                formation_type = "Mixed Defense"

            # Determine defensive line (where on the court the defense is set up)
            # This would need court coordinates to be meaningful
            # For now, use a placeholder approach
            y_positions = [p['position'][1] for p in player_positions]
            avg_y = sum(y_positions) / len(y_positions)
            court_height = court_dimensions[0]  # Length of the court

            if avg_y < court_height * 0.25:
                defensive_line = "Full Court"
            elif avg_y < court_height * 0.5:
                defensive_line = "3/4 Court"
            elif avg_y < court_height * 0.75:
                defensive_line = "Half Court"
            else:
                defensive_line = "Paint"

            # Calculate average defensive stance quality
            avg_stance_quality = sum(p.get('stance_quality', 0) for p in player_positions) / len(player_positions)

            # Determine pressure level based on spacing and stance quality
            if avg_spacing < 50 and avg_stance_quality > 7:  # Close spacing and good stance
                pressure_level = "High"
            elif avg_spacing < 100 and avg_stance_quality > 5:  # Medium spacing and decent stance
                pressure_level = "Medium"
            else:  # Wide spacing or poor stance
                pressure_level = "Low"

            # Calculate formation quality
            # This is a simplified approach and would need to be refined
            formation_quality = min(10, max(1, int((avg_stance_quality * 0.7 + (10 - avg_spacing/20) * 0.3))))

            return {
                "formation_type": formation_type,
                "spacing": avg_spacing,
                "defensive_line": defensive_line,
                "pressure_level": pressure_level,
                "formation_quality": formation_quality,
                "player_positions": player_positions,
                "clusters": {
                    "centers": cluster_centers.tolist(),
                    "labels": cluster_labels.tolist(),
                    "counts": cluster_counts.tolist()
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing team defensive formation: {e}")
            return {
                "formation_type": "Unknown",
                "spacing": 0,
                "defensive_line": "Unknown",
                "pressure_level": "Low",
                "formation_quality": 1,
                "error": str(e)
            }

    def analyze_defensive_matchups(self, defensive_players: List[Dict[str, Any]], offensive_players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze defensive matchups between defensive and offensive players.

        Args:
            defensive_players: List of defensive player detections with pose keypoints
            offensive_players: List of offensive player detections with pose keypoints

        Returns:
            List of matchup analyses
        """
        if not defensive_players or not offensive_players:
            return []

        try:
            matchups = []

            # Extract player positions
            def_positions = []
            for player in defensive_players:
                if 'keypoints' in player:
                    keypoints = player['keypoints']
                    try:
                        right_hip = keypoints[self.keypoint_indices["right_hip"]][:2]
                        left_hip = keypoints[self.keypoint_indices["left_hip"]][:2]
                        hip_center = [(right_hip[0] + left_hip[0]) / 2, (right_hip[1] + left_hip[1]) / 2]
                        def_positions.append({
                            'position': hip_center,
                            'player_id': player.get('id', 0),
                            'player': player
                        })
                    except (IndexError, KeyError):
                        if 'bbox' in player:
                            x1, y1, x2, y2 = player['bbox']
                            center = [(x1 + x2) / 2, (y1 + y2) / 2]
                            def_positions.append({
                                'position': center,
                                'player_id': player.get('id', 0),
                                'player': player
                            })

            off_positions = []
            for player in offensive_players:
                if 'keypoints' in player:
                    keypoints = player['keypoints']
                    try:
                        right_hip = keypoints[self.keypoint_indices["right_hip"]][:2]
                        left_hip = keypoints[self.keypoint_indices["left_hip"]][:2]
                        hip_center = [(right_hip[0] + left_hip[0]) / 2, (right_hip[1] + left_hip[1]) / 2]
                        off_positions.append({
                            'position': hip_center,
                            'player_id': player.get('id', 0),
                            'player': player
                        })
                    except (IndexError, KeyError):
                        if 'bbox' in player:
                            x1, y1, x2, y2 = player['bbox']
                            center = [(x1 + x2) / 2, (y1 + y2) / 2]
                            off_positions.append({
                                'position': center,
                                'player_id': player.get('id', 0),
                                'player': player
                            })

            # For each defensive player, find the closest offensive player
            for def_player in def_positions:
                closest_off_player = None
                min_distance = float('inf')

                for off_player in off_positions:
                    dist = math.sqrt(
                        (def_player['position'][0] - off_player['position'][0])**2 +
                        (def_player['position'][1] - off_player['position'][1])**2
                    )

                    if dist < min_distance:
                        min_distance = dist
                        closest_off_player = off_player

                if closest_off_player:
                    # Analyze the matchup
                    def_stance = None
                    if 'keypoints' in def_player['player']:
                        def_stance = self.analyze_defensive_stance(def_player['player']['keypoints'])

                    matchup_quality = 0
                    if def_stance:
                        # Good matchup has good stance and is close to offensive player
                        stance_quality = def_stance.get('stance_quality', 0)

                        # Distance factor (closer is better)
                        distance_factor = max(0, 10 - min_distance / 20)

                        # Orientation factor (facing the offensive player is better)
                        orientation_factor = 5  # Default neutral value
                        if 'keypoints' in def_player['player'] and 'keypoints' in closest_off_player['player']:
                            # Calculate orientation between defensive and offensive player
                            def_keypoints = def_player['player']['keypoints']
                            off_keypoints = closest_off_player['player']['keypoints']

                            try:
                                # Get defensive player's facing direction (shoulder line)
                                def_right_shoulder = def_keypoints[self.keypoint_indices["right_shoulder"]][:2]
                                def_left_shoulder = def_keypoints[self.keypoint_indices["left_shoulder"]][:2]
                                def_direction = [def_left_shoulder[0] - def_right_shoulder[0],
                                                def_left_shoulder[1] - def_right_shoulder[1]]

                                # Get vector from defensive to offensive player
                                off_vector = [closest_off_player['position'][0] - def_player['position'][0],
                                             closest_off_player['position'][1] - def_player['position'][1]]

                                # Calculate dot product for orientation
                                def_mag = math.sqrt(def_direction[0]**2 + def_direction[1]**2)
                                off_mag = math.sqrt(off_vector[0]**2 + off_vector[1]**2)

                                if def_mag > 0 and off_mag > 0:
                                    dot_product = (def_direction[0] * off_vector[0] + def_direction[1] * off_vector[1]) / (def_mag * off_mag)
                                    # Convert to angle (0 = perpendicular, 1 = same direction, -1 = opposite direction)
                                    # For defense, perpendicular is ideal (facing the player)
                                    orientation_factor = 10 - abs(dot_product) * 10
                            except (IndexError, KeyError):
                                pass

                        # Calculate overall matchup quality with orientation
                        matchup_quality = (stance_quality * 0.5 + distance_factor * 0.3 + orientation_factor * 0.2)
                    else:
                        # If no stance data, use distance only
                        matchup_quality = max(0, 10 - min_distance / 20)

                    # Normalize to 1-10 scale
                    matchup_quality = min(10, max(1, matchup_quality))

                    matchups.append({
                        'defensive_player_id': def_player['player_id'],
                        'offensive_player_id': closest_off_player['player_id'],
                        'distance': min_distance,
                        'matchup_quality': matchup_quality,
                        'defensive_stance': def_stance,
                        'orientation_factor': orientation_factor if 'orientation_factor' in locals() else 5
                    })

            return matchups
        except Exception as e:
            logger.error(f"Error analyzing defensive matchups: {e}")
            return []

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

    def _get_player_position(self, keypoints: List[List[float]]) -> List[float]:
        """
        Get player position from keypoints.

        Args:
            keypoints: List of pose keypoints [x, y, confidence]

        Returns:
            Player position as [x, y]
        """
        try:
            # Use hip center as player position
            right_hip = keypoints[self.keypoint_indices["right_hip"]][:2]
            left_hip = keypoints[self.keypoint_indices["left_hip"]][:2]
            return [(right_hip[0] + left_hip[0]) / 2, (right_hip[1] + left_hip[1]) / 2]
        except (IndexError, KeyError):
            # If hip keypoints are not available, use the average of all keypoints
            x_sum = sum(kp[0] for kp in keypoints if len(kp) >= 2)
            y_sum = sum(kp[1] for kp in keypoints if len(kp) >= 2)
            count = len(keypoints)
            if count > 0:
                return [x_sum / count, y_sum / count]
            else:
                return [0, 0]

# Create a singleton instance
# Try to use YOLOv8 if available, otherwise fall back to MediaPipe
try:
    from ultralytics import YOLO
    pose_estimator = PoseEstimator(model_type="yolov8")
    print("Using YOLOv8 for pose estimation")
except ImportError:
    pose_estimator = PoseEstimator(model_type="mediapipe")
    print("YOLOv8 not available, using MediaPipe for pose estimation")
