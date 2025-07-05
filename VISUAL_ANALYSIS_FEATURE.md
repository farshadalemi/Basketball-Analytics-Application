# Visual Analysis Feature

## Overview

The Basketball Analytics Application now includes **Visual Analysis** capabilities that provide annotated images showing detected basketball features overlaid on the original image.

## What's New

### 🎯 **Visual Image Analysis Endpoint**
- **Endpoint**: `POST /api/computer-vision/analyze-image-visual`
- **Returns**: Annotated image with visual highlights of detected features
- **Format**: JPEG image with overlays

### 🖼️ **Visual Features**

#### Court Detection Visualization
- **Green lines**: Court boundaries and corners
- **Blue lines**: Three-point line
- **Cyan circle**: Center circle
- **Green dots**: Corner points labeled C1, C2, C3, C4
- **Confidence score**: Displayed in top-left corner

#### Player Detection Visualization
- **Magenta boxes**: Player bounding boxes
- **Player IDs**: P1, P2, P3... with confidence scores
- **Jersey numbers**: Displayed below bounding boxes (when detected)
- **Player count**: Total players detected

#### Team Classification Visualization
- **Colored borders**: Different colors for each team
  - **Red**: Team 1
  - **Blue**: Team 2
  - **Gray**: Referees
  - **White**: Unknown/Unclassified
- **Team labels**: Team name with confidence score

#### Ball Detection Visualization
- **Orange circle**: Ball position with center dot
- **Confidence score**: Ball detection confidence
- **Velocity vector**: Arrow showing ball movement direction (when available)
- **Detection status**: "Ball: Detected" or "Ball: Not detected"

## How to Use

### Frontend Interface

1. **Navigate** to the Computer Vision Test page
2. **Select** an image using "Select Image" button
3. **Configure** analysis options (toggles for each feature type)
4. **Choose analysis type**:
   - **"Analyze (Data)"**: Returns JSON data with detection results
   - **"Analyze (Visual)"**: Returns annotated image with visual overlays

### API Usage

```bash
curl -X POST "http://localhost:8001/api/computer-vision/analyze-image-visual" \
  -F "image=@your_basketball_image.jpg" \
  -F "enable_court_detection=true" \
  -F "enable_player_detection=true" \
  -F "enable_team_classification=true" \
  -F "enable_ball_detection=true" \
  --output annotated_result.jpg
```

### Response Format

- **Content-Type**: `image/jpeg`
- **Headers**: `Content-Disposition: inline; filename=analyzed_image.jpg`
- **Body**: Binary JPEG image data with annotations

## Technical Implementation

### Backend Changes

1. **New Endpoint**: `/analyze-image-visual` in `computer_vision.py`
2. **Visualization Functions**:
   - `_draw_court_features()`: Court detection overlays
   - `_draw_player_detections()`: Player bounding boxes
   - `_draw_team_classifications()`: Team color coding
   - `_draw_ball_detection()`: Ball position and tracking

3. **Image Processing**: Uses OpenCV for drawing annotations
4. **Response Handling**: Returns image as StreamingResponse

### Frontend Changes

1. **New Button**: "Analyze (Visual)" button added
2. **Image Display**: Shows both original and annotated images
3. **API Integration**: New endpoint added to API configuration
4. **Memory Management**: Proper cleanup of blob URLs

## Benefits

### For Developers
- **Visual Debugging**: Immediately see what the AI detects
- **Algorithm Tuning**: Easily identify detection accuracy issues
- **Feature Validation**: Verify that detection algorithms work correctly

### For Users
- **Intuitive Results**: Visual feedback is easier to understand than JSON data
- **Quality Assessment**: Quickly evaluate detection quality
- **Educational**: Learn how computer vision algorithms "see" basketball scenes

### For Analysis
- **Presentation Ready**: Annotated images can be used in reports
- **Documentation**: Visual proof of detection capabilities
- **Comparison**: Easy to compare different algorithm configurations

## Example Use Cases

1. **Algorithm Development**: Test and refine detection algorithms
2. **Quality Control**: Verify detection accuracy on new datasets
3. **Demonstrations**: Show stakeholders what the system can detect
4. **Training Data**: Generate annotated images for machine learning
5. **Debugging**: Identify why certain detections fail

## Performance Considerations

- **Processing Time**: Visual analysis takes slightly longer due to drawing operations
- **Image Size**: Larger images take more time to process and annotate
- **Memory Usage**: Temporary image storage during annotation process
- **Network**: Annotated images are larger than JSON responses

## Future Enhancements

- **Customizable Colors**: Allow users to choose annotation colors
- **Annotation Density**: Options for minimal vs. detailed annotations
- **Export Formats**: Support for PNG, SVG, or other formats
- **Batch Processing**: Annotate multiple images at once
- **Video Annotations**: Extend visual analysis to video processing

## Testing

Use the provided test scripts:
- **PowerShell**: `test_visual_endpoint.ps1`
- **Python**: `test_visual_endpoint.py`

Or test manually through the frontend interface at `http://localhost:3000`

## Troubleshooting

### Common Issues

1. **No annotations visible**: Check if detection confidence thresholds are too high
2. **Poor detection quality**: Ensure good image quality and proper basketball court visibility
3. **Endpoint not found**: Verify scouting-service is running and updated
4. **Image not loading**: Check image format (JPEG/PNG supported)

### Debug Steps

1. Check scouting-service logs: `docker-compose logs scouting-service`
2. Test data endpoint first: `/analyze-image` should work before visual
3. Verify image upload: Ensure image file is valid and not corrupted
4. Check browser console: Look for JavaScript errors in frontend
