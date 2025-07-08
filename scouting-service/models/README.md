# Basketball Analysis Models

This directory should contain the following trained models for basketball video analysis:

## Required Models

1. **player_detector.pt** - YOLO model for detecting basketball players
   - Status: ✅ Available
   - Purpose: Detects and tracks players in basketball videos

2. **ball_detector_model.pt** - YOLO model for detecting basketballs
   - Status: ❌ Missing
   - Purpose: Detects and tracks the basketball in videos

3. **court_keypoint_detector.pt** - Model for detecting court keypoints
   - Status: ❌ Missing  
   - Purpose: Identifies court boundaries and key areas (3-point line, free throw line, etc.)

## Model Training

The missing models need to be trained using the training notebooks in the `training_notebooks/` directory:

- `basketball_ball_training.ipynb` - For training the ball detector
- `basketball_court_keypoint_training.ipynb` - For training the court keypoint detector

## Temporary Solution

For testing purposes, the service will use the player detector model for all detection tasks until the proper models are available. This will provide basic functionality but with reduced accuracy for ball and court detection.

## Model Sources

Models can be trained using:
- Custom datasets
- Roboflow datasets
- YOLO pre-trained models fine-tuned for basketball

Place the trained model files in this directory and ensure they match the filenames specified in `configs/configs.py`.
