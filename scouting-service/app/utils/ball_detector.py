"""Basketball detection and tracking for basketball videos."""
import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
import math

from app.core.logging import logger


class BallDetector:
    """Basketball detection and tracking."""
    
    def __init__(self):
        """Initialize the ball detector."""
        # Initialize ball tracking state
        self.prev_ball_positions = []
        self.ball_trajectory = []
        
        # Parameters for ball detection
        self.min_radius = 5
        self.max_radius = 30
        self.min_circularity = 0.7
        self.min_area = 100
    
    def detect_ball(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Detect the basketball in a frame.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Ball detection with position and radius, or None if no ball detected
        """
        try:
            # Convert to HSV color space
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Define range for orange color of basketball
            lower_orange = np.array([5, 100, 150])
            upper_orange = np.array([25, 255, 255])
            
            # Create mask and apply it
            mask = cv2.inRange(hsv, lower_orange, upper_orange)
            
            # Apply morphological operations to remove noise
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find the largest circular contour
            ball_position = None
            max_circularity = 0
            ball_radius = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_area:
                    perimeter = cv2.arcLength(contour, True)
                    circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                    
                    if circularity > self.min_circularity and circularity > max_circularity:
                        # Calculate radius from area
                        radius = np.sqrt(area / np.pi)
                        
                        if self.min_radius <= radius <= self.max_radius:
                            max_circularity = circularity
                            M = cv2.moments(contour)
                            if M["m00"] > 0:
                                cx = int(M["m10"] / M["m00"])
                                cy = int(M["m01"] / M["m00"])
                                ball_position = (cx, cy)
                                ball_radius = radius
            
            if ball_position:
                # Add to trajectory
                self.prev_ball_positions.append(ball_position)
                if len(self.prev_ball_positions) > 10:
                    self.prev_ball_positions.pop(0)
                
                return {
                    'position': ball_position,
                    'radius': ball_radius,
                    'confidence': max_circularity
                }
            
            return None
        except Exception as e:
            logger.error(f"Error in ball detection: {e}")
            return None
    
    def track_ball(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Track the basketball across frames.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Ball tracking data with position, velocity, and trajectory
        """
        # Detect ball in current frame
        ball_detection = self.detect_ball(frame)
        
        if not ball_detection:
            # If no ball detected, try to predict from previous positions
            if len(self.prev_ball_positions) >= 2:
                # Simple linear prediction
                last_pos = self.prev_ball_positions[-1]
                prev_pos = self.prev_ball_positions[-2]
                
                # Calculate velocity
                vx = last_pos[0] - prev_pos[0]
                vy = last_pos[1] - prev_pos[1]
                
                # Predict new position
                predicted_x = last_pos[0] + vx
                predicted_y = last_pos[1] + vy
                
                # Add to trajectory with lower confidence
                predicted_position = (int(predicted_x), int(predicted_y))
                self.prev_ball_positions.append(predicted_position)
                if len(self.prev_ball_positions) > 10:
                    self.prev_ball_positions.pop(0)
                
                return {
                    'position': predicted_position,
                    'radius': 10,  # Default radius
                    'confidence': 0.3,  # Lower confidence for prediction
                    'is_predicted': True
                }
            return None
        
        # Calculate velocity if we have previous positions
        velocity = None
        if len(self.prev_ball_positions) >= 2:
            last_pos = self.prev_ball_positions[-1]
            current_pos = ball_detection['position']
            
            vx = current_pos[0] - last_pos[0]
            vy = current_pos[1] - last_pos[1]
            velocity = (vx, vy)
        
        # Add trajectory data
        return {
            **ball_detection,
            'velocity': velocity,
            'trajectory': self.prev_ball_positions.copy(),
            'is_predicted': False
        }
    
    def detect_shot(self, ball_tracking: List[Dict[str, Any]], court_info: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Detect shot attempts from ball trajectory.
        
        Args:
            ball_tracking: List of ball tracking data for consecutive frames
            court_info: Court information including basket locations
            
        Returns:
            List of detected shots with start/end frames and outcome
        """
        if len(ball_tracking) < 10:
            return []
        
        shots = []
        
        # Default basket locations if not provided
        if court_info is None or 'baskets' not in court_info:
            # Assume baskets are at the horizontal center, near the vertical edges
            frame_height = 720  # Default height
            frame_width = 1280  # Default width
            
            # Get frame dimensions from the first valid ball tracking
            for tracking in ball_tracking:
                if tracking and 'position' in tracking:
                    position = tracking['position']
                    frame_width = max(frame_width, position[0] * 2)
                    frame_height = max(frame_height, position[1] * 2)
                    break
            
            court_info = {
                'baskets': [
                    {'position': (frame_width // 2, 50)},  # Top basket
                    {'position': (frame_width // 2, frame_height - 50)}  # Bottom basket
                ]
            }
        
        # Analyze trajectory for shot patterns
        # A shot typically has: upward motion, peak, downward motion
        
        # Find peaks in the trajectory (where y velocity changes from positive to negative)
        peaks = []
        for i in range(1, len(ball_tracking) - 1):
            prev_tracking = ball_tracking[i-1]
            curr_tracking = ball_tracking[i]
            next_tracking = ball_tracking[i+1]
            
            if (prev_tracking and curr_tracking and next_tracking and
                'velocity' in prev_tracking and 'velocity' in curr_tracking and
                prev_tracking['velocity'] and curr_tracking['velocity']):
                
                prev_vy = prev_tracking['velocity'][1]
                curr_vy = curr_tracking['velocity'][1]
                
                # Detect peak (y velocity changes from negative to positive)
                if prev_vy < 0 and curr_vy >= 0:
                    peaks.append(i)
        
        # For each peak, check if it's a shot
        for peak_idx in peaks:
            # Look back for shot start
            shot_start_idx = max(0, peak_idx - 15)
            
            # Look forward for shot end
            shot_end_idx = min(len(ball_tracking) - 1, peak_idx + 15)
            
            # Check if the ball is near a basket at the end
            is_near_basket = False
            made_shot = False
            basket_idx = -1
            
            for i in range(peak_idx, shot_end_idx + 1):
                if i >= len(ball_tracking) or not ball_tracking[i] or 'position' not in ball_tracking[i]:
                    continue
                
                ball_pos = ball_tracking[i]['position']
                
                # Check distance to each basket
                for j, basket in enumerate(court_info['baskets']):
                    basket_pos = basket['position']
                    distance = math.sqrt((ball_pos[0] - basket_pos[0])**2 + (ball_pos[1] - basket_pos[1])**2)
                    
                    if distance < 50:  # Threshold for being near basket
                        is_near_basket = True
                        basket_idx = j
                        
                        # Check if the ball goes through the basket
                        # This is a simplified check - in reality, you'd need more sophisticated detection
                        if i < shot_end_idx and ball_tracking[i+1] and 'position' in ball_tracking[i+1]:
                            next_pos = ball_tracking[i+1]['position']
                            if next_pos[1] > ball_pos[1] + 10:  # Ball continues downward after basket
                                made_shot = True
                        
                        break
                
                if is_near_basket:
                    break
            
            # If the ball trajectory goes near a basket, consider it a shot
            if is_near_basket:
                shot = {
                    'start_frame': shot_start_idx,
                    'peak_frame': peak_idx,
                    'end_frame': shot_end_idx,
                    'basket_idx': basket_idx,
                    'made': made_shot,
                    'confidence': 0.7  # Confidence in shot detection
                }
                
                # Calculate shot position (at peak)
                if ball_tracking[peak_idx] and 'position' in ball_tracking[peak_idx]:
                    shot['position'] = ball_tracking[peak_idx]['position']
                
                shots.append(shot)
        
        return shots


# Create a singleton instance
ball_detector = BallDetector()
