"""Utility for processing large video files in chunks."""
import os
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

from app.core.logging import logger


class VideoChunker:
    """Utility for processing large video files in chunks."""
    
    def __init__(self, chunk_size_seconds: int = 60):
        """
        Initialize the video chunker.
        
        Args:
            chunk_size_seconds: Size of each chunk in seconds
        """
        self.chunk_size_seconds = chunk_size_seconds
    
    def split_video(self, video_path: str, output_dir: str) -> List[str]:
        """
        Split a video into chunks.
        
        Args:
            video_path: Path to the video file
            output_dir: Directory to save the chunks
            
        Returns:
            List of paths to the chunk files
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Open the video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Video properties: {fps} fps, {width}x{height}, {total_frames} frames")
        
        # Calculate chunk size in frames
        chunk_size_frames = int(fps * self.chunk_size_seconds)
        
        # Calculate number of chunks
        num_chunks = (total_frames + chunk_size_frames - 1) // chunk_size_frames
        
        chunk_paths = []
        
        for i in range(num_chunks):
            # Create output file for this chunk
            chunk_path = os.path.join(output_dir, f"chunk_{i:04d}.mp4")
            chunk_paths.append(chunk_path)
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(chunk_path, fourcc, fps, (width, height))
            
            # Write frames for this chunk
            frames_to_write = min(chunk_size_frames, total_frames - i * chunk_size_frames)
            
            for _ in range(frames_to_write):
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
            
            # Release the writer
            out.release()
            
            logger.info(f"Created chunk {i+1}/{num_chunks}: {chunk_path}")
        
        # Release the video capture
        cap.release()
        
        return chunk_paths
    
    def get_chunk_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        Get metadata for a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary of video metadata
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        # Release the video capture
        cap.release()
        
        metadata = {
            "fps": fps,
            "width": width,
            "height": height,
            "total_frames": total_frames,
            "duration": duration,
            "chunk_size_seconds": self.chunk_size_seconds,
            "estimated_chunks": (duration + self.chunk_size_seconds - 1) // self.chunk_size_seconds
        }
        
        logger.info(f"Video metadata: {metadata}")
        
        return metadata


# Create a singleton instance
video_chunker = VideoChunker()
