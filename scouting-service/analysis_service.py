"""
Analysis Service - Wraps the existing basketball analysis pipeline
"""
import os
import asyncio
import traceback
from typing import Dict, Optional, List
from pathlib import Path
import json

from utils import read_video, save_video
from trackers import PlayerTracker, BallTracker
from team_assigner import TeamAssigner
from court_keypoint_detector import CourtKeypointDetector
from ball_aquisition import BallAquisitionDetector
from pass_and_interception_detector import PassAndInterceptionDetector
from tactical_view_converter import TacticalViewConverter
from speed_and_distance_calculator import SpeedAndDistanceCalculator
from drawers import (
    PlayerTracksDrawer, 
    BallTracksDrawer,
    CourtKeypointDrawer,
    TeamBallControlDrawer,
    FrameNumberDrawer,
    PassInterceptionDrawer,
    TacticalViewDrawer,
    SpeedAndDistanceDrawer
)
from configs import(
    STUBS_DEFAULT_PATH,
    PLAYER_DETECTOR_PATH,
    BALL_DETECTOR_PATH,
    COURT_KEYPOINT_DETECTOR_PATH,
    OUTPUT_VIDEO_PATH
)

class AnalysisService:
    """Service for managing basketball video analysis jobs"""
    
    def __init__(self):
        self.jobs = {}  # In-memory job storage (use database in production)
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize all analysis models"""
        try:
            # Initialize player tracker (required)
            if not os.path.exists(PLAYER_DETECTOR_PATH):
                raise FileNotFoundError(f"Player detector model not found: {PLAYER_DETECTOR_PATH}")
            self.player_tracker = PlayerTracker(PLAYER_DETECTOR_PATH)

            # Initialize ball tracker (use player detector as fallback)
            ball_model_path = BALL_DETECTOR_PATH if os.path.exists(BALL_DETECTOR_PATH) else PLAYER_DETECTOR_PATH
            if ball_model_path != BALL_DETECTOR_PATH:
                print(f"Warning: Ball detector model not found, using player detector as fallback")
            self.ball_tracker = BallTracker(ball_model_path)

            # Initialize court keypoint detector (use player detector as fallback)
            court_model_path = COURT_KEYPOINT_DETECTOR_PATH if os.path.exists(COURT_KEYPOINT_DETECTOR_PATH) else PLAYER_DETECTOR_PATH
            if court_model_path != COURT_KEYPOINT_DETECTOR_PATH:
                print(f"Warning: Court keypoint detector model not found, using player detector as fallback")
            self.court_keypoint_detector = CourtKeypointDetector(court_model_path)

            self.team_assigner = TeamAssigner()
            self.ball_aquisition_detector = BallAquisitionDetector()
            self.pass_and_interception_detector = PassAndInterceptionDetector()
            
            # Initialize drawers
            self.player_tracks_drawer = PlayerTracksDrawer()
            self.ball_tracks_drawer = BallTracksDrawer()
            self.court_keypoint_drawer = CourtKeypointDrawer()
            self.team_ball_control_drawer = TeamBallControlDrawer()
            self.frame_number_drawer = FrameNumberDrawer()
            self.pass_and_interceptions_drawer = PassInterceptionDrawer()
            self.tactical_view_drawer = TacticalViewDrawer()
            self.speed_and_distance_drawer = SpeedAndDistanceDrawer()
            
            print("Analysis models initialized successfully")
            
        except Exception as e:
            print(f"Error initializing models: {str(e)}")
            traceback.print_exc()
    
    async def analyze_video(self, job_id: str, video_path: str, options: Dict):
        """
        Perform video analysis (runs in background)
        """
        try:
            # Update job status
            self.jobs[job_id] = {
                "job_id": job_id,
                "status": "running",
                "progress": 0,
                "message": "Starting analysis..."
            }

            # Download video from MinIO to local temp file
            local_video_path = await self._download_video_from_minio(video_path, job_id)

            # Read video
            self.jobs[job_id]["message"] = "Reading video..."
            self.jobs[job_id]["progress"] = 10
            video_frames = read_video(local_video_path)
            
            # Create stub directory for this job
            stub_path = os.path.join(STUBS_DEFAULT_PATH, job_id)
            os.makedirs(stub_path, exist_ok=True)
            
            # Run player tracking
            self.jobs[job_id]["message"] = "Tracking players..."
            self.jobs[job_id]["progress"] = 20
            player_tracks = self.player_tracker.get_object_tracks(
                video_frames,
                read_from_stub=False,  # Always process fresh
                stub_path=os.path.join(stub_path, 'player_track_stubs.pkl')
            )
            
            # Run ball tracking
            self.jobs[job_id]["message"] = "Tracking ball..."
            self.jobs[job_id]["progress"] = 30
            ball_tracks = self.ball_tracker.get_object_tracks(
                video_frames,
                read_from_stub=False,
                stub_path=os.path.join(stub_path, 'ball_track_stubs.pkl')
            )
            
            # Extract court keypoints
            self.jobs[job_id]["message"] = "Detecting court keypoints..."
            self.jobs[job_id]["progress"] = 40
            court_keypoints_per_frame = self.court_keypoint_detector.get_court_keypoints(
                video_frames,
                read_from_stub=False,
                stub_path=os.path.join(stub_path, 'court_key_points_stub.pkl')
            )
            
            # Process ball tracks
            self.jobs[job_id]["message"] = "Processing ball detections..."
            self.jobs[job_id]["progress"] = 50
            ball_tracks = self.ball_tracker.remove_wrong_detections(ball_tracks)
            ball_tracks = self.ball_tracker.interpolate_ball_positions(ball_tracks)
            
            # Assign player teams
            self.jobs[job_id]["message"] = "Assigning player teams..."
            self.jobs[job_id]["progress"] = 60
            player_assignment = self.team_assigner.get_player_teams_across_frames(
                video_frames,
                player_tracks,
                read_from_stub=False,
                stub_path=os.path.join(stub_path, 'player_assignment_stub.pkl')
            )
            
            # Detect ball possession
            self.jobs[job_id]["message"] = "Analyzing ball possession..."
            self.jobs[job_id]["progress"] = 70
            ball_aquisition = self.ball_aquisition_detector.detect_ball_possession(player_tracks, ball_tracks)
            
            # Detect passes and interceptions
            passes = self.pass_and_interception_detector.detect_passes(ball_aquisition, player_assignment)
            interceptions = self.pass_and_interception_detector.detect_interceptions(ball_aquisition, player_assignment)
            
            # Tactical view analysis
            self.jobs[job_id]["message"] = "Creating tactical view..."
            self.jobs[job_id]["progress"] = 80
            tactical_view_converter = TacticalViewConverter(
                court_image_path="./images/basketball_court.png"
            )
            court_keypoints_per_frame = tactical_view_converter.validate_keypoints(court_keypoints_per_frame)
            tactical_player_positions = tactical_view_converter.transform_players_to_tactical_view(
                court_keypoints_per_frame, player_tracks
            )
            
            # Speed and distance calculations
            speed_and_distance_calculator = SpeedAndDistanceCalculator(
                tactical_view_converter.width,
                tactical_view_converter.height,
                tactical_view_converter.actual_width_in_meters,
                tactical_view_converter.actual_height_in_meters
            )
            player_distances_per_frame = speed_and_distance_calculator.calculate_distance(tactical_player_positions)
            player_speed_per_frame = speed_and_distance_calculator.calculate_speed(player_distances_per_frame)
            
            # Draw analysis results
            self.jobs[job_id]["message"] = "Rendering analysis..."
            self.jobs[job_id]["progress"] = 90
            output_video_frames = self._draw_analysis_results(
                video_frames, player_tracks, ball_tracks, court_keypoints_per_frame,
                player_assignment, ball_aquisition, passes, interceptions,
                tactical_view_converter, tactical_player_positions,
                player_distances_per_frame, player_speed_per_frame
            )
            
            # Save output video
            output_path = os.path.join("output_videos", f"analysis_{job_id}.mp4")
            os.makedirs("output_videos", exist_ok=True)
            save_video(output_video_frames, output_path)
            
            # Save analysis metadata
            metadata = {
                "job_id": job_id,
                "video_path": video_path,
                "output_path": output_path,
                "analysis_summary": {
                    "total_frames": len(video_frames),
                    "players_detected": len(set([track_id for frame_tracks in player_tracks for track_id in frame_tracks.keys()])),
                    "passes_detected": len(passes),
                    "interceptions_detected": len(interceptions)
                }
            }
            
            metadata_path = os.path.join("output_videos", f"metadata_{job_id}.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Update job status
            self.jobs[job_id] = {
                "job_id": job_id,
                "status": "completed",
                "progress": 100,
                "message": "Analysis completed successfully",
                "result_path": output_path,
                "metadata_path": metadata_path
            }
            
        except Exception as e:
            # Update job with error status
            self.jobs[job_id] = {
                "job_id": job_id,
                "status": "failed",
                "progress": 0,
                "message": "Analysis failed",
                "error": str(e)
            }
            print(f"Analysis failed for job {job_id}: {str(e)}")
            traceback.print_exc()
    
    def _draw_analysis_results(self, video_frames, player_tracks, ball_tracks, 
                             court_keypoints_per_frame, player_assignment, ball_aquisition,
                             passes, interceptions, tactical_view_converter, 
                             tactical_player_positions, player_distances_per_frame, 
                             player_speed_per_frame):
        """Draw all analysis results on video frames"""
        
        # Draw player tracks
        output_video_frames = self.player_tracks_drawer.draw(
            video_frames, player_tracks, player_assignment, ball_aquisition
        )
        
        # Draw ball tracks
        output_video_frames = self.ball_tracks_drawer.draw(output_video_frames, ball_tracks)
        
        # Draw court keypoints
        output_video_frames = self.court_keypoint_drawer.draw(output_video_frames, court_keypoints_per_frame)
        
        # Draw frame numbers
        output_video_frames = self.frame_number_drawer.draw(output_video_frames)
        
        # Draw team ball control
        output_video_frames = self.team_ball_control_drawer.draw(
            output_video_frames, player_assignment, ball_aquisition
        )
        
        # Draw passes and interceptions
        output_video_frames = self.pass_and_interceptions_drawer.draw(
            output_video_frames, passes, interceptions
        )
        
        # Draw speed and distance
        output_video_frames = self.speed_and_distance_drawer.draw(
            output_video_frames, player_tracks, player_distances_per_frame, player_speed_per_frame
        )
        
        # Draw tactical view
        output_video_frames = self.tactical_view_drawer.draw(
            output_video_frames,
            tactical_view_converter.court_image_path,
            tactical_view_converter.width,
            tactical_view_converter.height,
            tactical_view_converter.key_points,
            tactical_player_positions,
            player_assignment,
            ball_aquisition
        )
        
        return output_video_frames
    
    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status"""
        return self.jobs.get(job_id)
    
    async def get_result_path(self, job_id: str) -> Optional[str]:
        """Get result file path"""
        job = self.jobs.get(job_id)
        if job and job.get("status") == "completed":
            return job.get("result_path")
        return None
    
    async def list_jobs(self) -> List[Dict]:
        """List all jobs"""
        return list(self.jobs.values())
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete job and cleanup files"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        # Cleanup files
        if "result_path" in job and os.path.exists(job["result_path"]):
            os.remove(job["result_path"])
        
        if "metadata_path" in job and os.path.exists(job["metadata_path"]):
            os.remove(job["metadata_path"])
        
        # Remove job from memory
        del self.jobs[job_id]
        
        return True

    async def _download_video_from_minio(self, video_path: str, job_id: str) -> str:
        """
        Download video from MinIO to local temporary file

        Args:
            video_path: Path to video in MinIO
            job_id: Job ID for unique filename

        Returns:
            Local path to downloaded video file
        """
        try:
            from minio import Minio
            from config import settings

            # Initialize MinIO client
            client = Minio(
                settings.MINIO_URL,
                access_key=settings.MINIO_ROOT_USER,
                secret_key=settings.MINIO_ROOT_PASSWORD,
                secure=False
            )

            # Create local temp directory
            temp_dir = os.path.join("input_videos", job_id)
            os.makedirs(temp_dir, exist_ok=True)

            # Extract filename from video_path
            filename = os.path.basename(video_path)
            if not filename:
                filename = f"video_{job_id}.mp4"

            local_path = os.path.join(temp_dir, filename)

            # Download file from MinIO
            client.fget_object(
                bucket_name=settings.MINIO_BUCKET,
                object_name=video_path,
                file_path=local_path
            )

            print(f"Downloaded video from MinIO: {video_path} -> {local_path}")
            return local_path

        except Exception as e:
            raise Exception(f"Failed to download video from MinIO: {str(e)}")
