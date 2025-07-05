#!/usr/bin/env python3
"""
Test script for the visual image analysis endpoint.
"""
import requests
import os
from pathlib import Path

def test_visual_endpoint():
    """Test the visual image analysis endpoint."""
    
    # Create a simple test image if none exists
    test_image_path = "test_image.jpg"
    
    if not os.path.exists(test_image_path):
        print("Creating a simple test image...")
        try:
            import cv2
            import numpy as np
            
            # Create a simple basketball court-like image
            img = np.zeros((400, 600, 3), dtype=np.uint8)
            img.fill(34)  # Dark background
            
            # Draw court lines
            cv2.rectangle(img, (50, 50), (550, 350), (255, 255, 255), 2)  # Court boundary
            cv2.circle(img, (300, 200), 50, (255, 255, 255), 2)  # Center circle
            cv2.line(img, (300, 50), (300, 350), (255, 255, 255), 2)  # Center line
            
            # Add some player-like rectangles
            cv2.rectangle(img, (150, 150), (180, 220), (0, 255, 0), -1)  # Player 1
            cv2.rectangle(img, (420, 180), (450, 250), (0, 0, 255), -1)  # Player 2
            
            # Add a ball-like circle
            cv2.circle(img, (250, 180), 8, (0, 165, 255), -1)  # Orange ball
            
            cv2.imwrite(test_image_path, img)
            print(f"Created test image: {test_image_path}")
            
        except ImportError:
            print("OpenCV not available, please provide a test image manually")
            return False
    
    # Test the visual endpoint
    url = "http://localhost:8001/api/computer-vision/analyze-image-visual"
    
    try:
        with open(test_image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'enable_court_detection': 'true',
                'enable_player_detection': 'true',
                'enable_team_classification': 'true',
                'enable_ball_detection': 'true'
            }
            
            print("Sending request to visual analysis endpoint...")
            response = requests.post(url, files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                # Save the annotated image
                output_path = "annotated_result.jpg"
                with open(output_path, 'wb') as out_file:
                    out_file.write(response.content)
                
                print(f"✅ Success! Annotated image saved as: {output_path}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                print(f"Image size: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Visual Image Analysis Endpoint")
    print("=" * 40)
    
    success = test_visual_endpoint()
    
    if success:
        print("\n🎉 Visual endpoint is working correctly!")
        print("You can now use the frontend to upload images and see visual analysis results.")
    else:
        print("\n💥 Visual endpoint test failed.")
        print("Please check the scouting-service logs for more details.")
