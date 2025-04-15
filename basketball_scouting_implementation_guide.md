# Getting Real Reports from the Scouting Service

To get real, comprehensive reports from the scouting service based on full game analysis (40 minutes of play time in a ~2 hour video), you'll need to enhance the service to handle real game footage and perform actual analysis rather than generating mock data. Here's a detailed plan for implementing this:

## 1. Video Processing Infrastructure

### A. Video Ingestion and Storage
- Configure the MinIO storage to handle large video files (2+ hours)
- Implement chunking for large video uploads to prevent timeouts
- Add video format validation and conversion if needed

```bash
# Example configuration for MinIO to handle large files
# Add to your docker-compose.yml for the minio service
environment:
  - MINIO_BROWSER_REDIRECT_URL=http://localhost:9001
  - MINIO_DOMAIN=localhost
  - MINIO_CORS_ALLOW_ALL=true
  - MINIO_BROWSER=on
  - MINIO_REGION=us-east-1
  - MINIO_API_CORS_ALLOW_ORIGIN=*
  # Add these for large file handling
  - MINIO_COMPRESS=true
  - MINIO_COMPRESS_EXTENSIONS=.mp4,.avi,.mov
  - MINIO_COMPRESS_MIME_TYPES=video/mp4,video/x-msvideo,video/quicktime
```

### B. Video Processing Pipeline
- Implement a distributed processing pipeline using Celery or similar
- Set up worker nodes that can process video segments in parallel
- Configure timeouts and retries for long-running tasks

## 2. Computer Vision Implementation

### A. Player Detection and Tracking
- Replace the mock player detection with actual OpenCV or YOLOv8 implementation
- Implement player tracking across frames using algorithms like SORT or DeepSORT
- Add jersey number recognition using OCR (Tesseract) or a custom CNN

```python
# Example code for player detection with YOLOv8
from ultralytics import YOLO

class PlayerDetector:
    def __init__(self):
        self.model = YOLO('yolov8x.pt')  # Load YOLOv8 model
        
    def detect_players(self, frame):
        results = self.model(frame, classes=[0])  # Class 0 is person
        players = []
        
        for i, detection in enumerate(results[0].boxes.data):
            x1, y1, x2, y2, conf, cls = detection
            if conf > 0.5:  # Confidence threshold
                players.append({
                    'id': i,
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'confidence': float(conf)
                })
                
        return players
```

### B. Pose Estimation
- Implement the pose estimation using OpenPose, MediaPipe, or YOLOv8-pose
- Track player joints and body positions for stance and movement analysis
- Calculate biomechanical metrics for player movement

### C. Ball Tracking
- Implement ball detection and tracking using Hough Circle Transform or a specialized model
- Track ball possession changes between players
- Detect shot attempts, passes, and dribbles

```python
# Example code for ball tracking
import cv2
import numpy as np

def detect_basketball(frame):
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
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:  # Minimum area threshold
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            if circularity > 0.7 and circularity > max_circularity:  # Threshold for circularity
                max_circularity = circularity
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    ball_position = (cx, cy)
    
    return ball_position
```

### D. Court Detection
- Implement court line detection to establish a coordinate system
- Map player positions to court coordinates
- Enable zone-based analysis (paint, mid-range, 3-point, etc.)

## 3. Game Analysis Algorithms

### A. Play Detection
- Implement algorithms to detect different play types (pick and roll, isolation, etc.)
- Use machine learning to classify plays based on player movements
- Track play outcomes for effectiveness analysis

```python
# Example pseudocode for play detection
def detect_pick_and_roll(player_positions, frames):
    """
    Detect pick and roll plays from player position data
    """
    for i in range(len(frames) - 30):  # Look at 30-frame windows
        ball_handler = find_ball_handler(frames[i:i+30])
        if ball_handler:
            # Check if another player comes to set a screen
            screener = find_screener_for_ball_handler(ball_handler, frames[i:i+30])
            if screener:
                # Check if ball handler uses the screen
                if ball_handler_uses_screen(ball_handler, screener, frames[i:i+30]):
                    # Check if screener rolls to the basket
                    if screener_rolls_to_basket(screener, frames[i:i+30]):
                        return {
                            'play_type': 'Pick and Roll',
                            'start_frame': i,
                            'end_frame': i+30,
                            'ball_handler': ball_handler['id'],
                            'screener': screener['id']
                        }
    return None
```

### B. Shot Analysis
- Detect shot attempts and outcomes (make/miss)
- Calculate shooting percentages by zone, player, and play type
- Generate shot charts with hotspots and cold zones

### C. Defensive Analysis
- Implement algorithms to detect defensive schemes (man-to-man, zone, etc.)
- Analyze defensive rotations, help defense, and closeouts
- Calculate defensive metrics (opponent field goal percentage, etc.)

### D. Advanced Metrics Calculation
- Implement algorithms to calculate advanced metrics (offensive rating, defensive rating, etc.)
- Track lineup effectiveness
- Calculate player impact metrics

## 4. Machine Learning Models

### A. Play Classification Model
- Train a model to classify play types from player movement data
- Use supervised learning with labeled play data
- Implement feature extraction for player movements and interactions

```python
# Example pseudocode for play classification model
from sklearn.ensemble import RandomForestClassifier
import numpy as np

class PlayClassifier:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        
    def train(self, play_sequences, labels):
        """
        Train the model on play sequences
        
        play_sequences: List of player movement sequences
        labels: Play type labels (e.g., 'Pick and Roll', 'Isolation')
        """
        # Extract features from play sequences
        features = np.array([self._extract_features(seq) for seq in play_sequences])
        
        # Train the model
        self.model.fit(features, labels)
        
    def predict(self, play_sequence):
        """
        Predict the play type from a sequence
        """
        features = self._extract_features(play_sequence)
        return self.model.predict([features])[0]
        
    def _extract_features(self, play_sequence):
        """
        Extract features from a play sequence
        """
        # Example features:
        # - Distance between players
        # - Player velocities
        # - Ball movement
        # - Court positions
        # ...
        features = []
        
        # Calculate features
        # ...
        
        return features
```

### B. Defensive Scheme Recognition
- Train a model to recognize defensive schemes from player positioning
- Implement real-time scheme detection during video processing
- Track scheme changes throughout the game

### C. Player Role Classification
- Train a model to identify player roles (point guard, shooting guard, etc.)
- Use player movement patterns and actions to determine roles
- Adapt analysis based on identified roles

## 5. Report Generation

### A. Enhanced PDF Generation
- Improve the PDF generator to include actual analysis results
- Add visualizations (shot charts, heatmaps, etc.)
- Include video clips of key plays

```python
# Example code for adding a shot chart to the PDF
def add_shot_chart(content, shot_data, styles):
    """
    Add a shot chart visualization to the PDF
    """
    # Create a matplotlib figure for the shot chart
    fig = plt.figure(figsize=(8, 7.5))
    ax = fig.add_subplot(111)
    
    # Draw the court
    draw_court(ax)
    
    # Plot shots
    for shot in shot_data:
        x, y = shot['x'], shot['y']
        made = shot['made']
        
        # Plot made shots as green, missed as red
        color = 'green' if made else 'red'
        marker = 'o' if made else 'x'
        
        ax.plot(x, y, marker=marker, color=color, markersize=8, alpha=0.7)
    
    # Save the figure to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    
    # Add the image to the PDF
    img = Image(buf, width=6*inch, height=5.5*inch)
    content.append(img)
    content.append(Spacer(1, 0.25*inch))
    
    return content
```

### B. Interactive Web Reports
- Develop a web-based report viewer with interactive elements
- Allow users to filter and drill down into specific aspects of the analysis
- Include video playback synchronized with analysis data

### C. Video Highlight Generation
- Automatically generate highlight clips of key plays
- Include annotations and analysis overlays
- Provide downloadable highlight packages

## 6. Performance Optimization

### A. GPU Acceleration
- Configure the system to use GPU acceleration for computer vision tasks
- Optimize models for GPU execution
- Implement batch processing for efficiency

```bash
# Example Docker configuration for GPU support
# Add to your docker-compose.yml for the scouting-service
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### B. Distributed Processing
- Set up a cluster for distributed video processing
- Implement job queuing and load balancing
- Configure auto-scaling based on workload

### C. Incremental Processing
- Implement incremental processing to provide partial results while analysis continues
- Add progress tracking and estimation
- Allow users to view preliminary reports before full analysis completes

## 7. Testing and Validation

### A. Ground Truth Dataset
- Create a labeled dataset of basketball plays and events
- Use professional analysts to validate the labels
- Measure algorithm performance against ground truth

### B. Accuracy Metrics
- Implement metrics to measure detection and classification accuracy
- Track false positives and false negatives
- Continuously improve models based on accuracy metrics

### C. User Feedback Loop
- Add a feedback mechanism for users to rate report accuracy
- Collect annotations and corrections from users
- Use feedback to improve models and algorithms

## Implementation Timeline

1. **Phase 1 (1-2 months)**: Basic video processing pipeline and player detection
2. **Phase 2 (2-3 months)**: Pose estimation, ball tracking, and court detection
3. **Phase 3 (3-4 months)**: Play detection and shot analysis
4. **Phase 4 (2-3 months)**: Defensive analysis and advanced metrics
5. **Phase 5 (2-3 months)**: Machine learning model training and integration
6. **Phase 6 (1-2 months)**: Enhanced report generation
7. **Phase 7 (1-2 months)**: Performance optimization and testing

## Resources Required

1. **Hardware**:
   - GPU-equipped servers for video processing
   - Storage infrastructure for video files
   - Development workstations with GPUs

2. **Software**:
   - Computer vision libraries (OpenCV, YOLOv8, MediaPipe)
   - Machine learning frameworks (TensorFlow, PyTorch)
   - Distributed processing tools (Celery, Redis)

3. **Data**:
   - Basketball game footage for training and testing
   - Labeled play datasets
   - Professional basketball analytics resources

4. **Expertise**:
   - Computer vision engineers
   - Machine learning specialists
   - Basketball analytics experts
   - Full-stack developers

By following this implementation plan, you can transform your scouting service from generating mock reports to producing real, data-driven analysis of full basketball games. This will provide coaches and analysts with valuable insights that can help improve team performance and game strategy.
