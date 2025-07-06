"""
Computer Vision API endpoints for basketball analytics.

This module provides REST API endpoints for:
- Video processing with computer vision
- Player detection and tracking
- Team classification
- Court detection
- Real-time analysis results
"""

from typing import Dict, List, Any, Optional
import asyncio
import tempfile
import os
import io
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
import httpx
import cv2
import numpy as np

from app.db.session import get_db
from app.core.logging import logger
from app.api.responses import ResponseModel


def convert_numpy_types(obj):
    """
    Convert numpy types to Python native types recursively for JSON serialization.

    Args:
        obj: Object that may contain numpy types

    Returns:
        Object with numpy types converted to Python native types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    else:
        return obj


# Import services
from app.services.video_processing import (
    VideoProcessor,
    VideoProcessingConfig,
    get_job_manager
)
from app.services.player_tracking import PlayerDetector, TeamClassifier
from app.services.ball_detection import BallDetector
from app.services.court_detection import SimplifiedCourtDetector
from app.models.computer_vision import VideoProcessingJob

router = APIRouter(prefix="/computer-vision", tags=["Computer Vision"])


@router.post("/process-video", response_model=Dict[str, Any])
async def process_video(
    *,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks,
    video_id: int = Form(...),
    config: Optional[str] = Form(None),  # JSON string of processing config
) -> Dict[str, Any]:
    """
    Start computer vision processing for a video.
    
    This endpoint initiates comprehensive computer vision analysis including:
    - Court detection and feature recognition
    - Player detection and tracking
    - Team classification
    - Ball detection and tracking
    - Formation analysis
    """
    try:
        logger.info(f"Starting computer vision processing for video {video_id}")
        
        # Parse processing configuration
        processing_config = VideoProcessingConfig()
        if config:
            import json
            config_dict = json.loads(config)
            processing_config = VideoProcessingConfig(**config_dict)
        
        # Get video data from main backend
        video_data = await _get_video_data(video_id)
        if not video_data:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Create processing job in database
        job = VideoProcessingJob(
            video_id=video_id,
            status="queued",
            processing_config=processing_config.__dict__
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Submit job to processing queue
        job_manager = get_job_manager()
        await job_manager.submit_job(
            video_id=video_id,
            video_path=video_data.get('file_path', ''),
            config=processing_config
        )
        
        logger.info(f"Computer vision job {job.id} queued for video {video_id}")
        
        return ResponseModel.success(
            data={
                "job_id": job.id,
                "video_id": video_id,
                "status": job.status,
                "message": "Computer vision processing started"
            },
            message="Video processing job created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error starting video processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_status(
    job_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get the status and progress of a computer vision processing job."""
    try:
        job = db.query(VideoProcessingJob).filter(VideoProcessingJob.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return ResponseModel.success(
            data={
                "job_id": job.id,
                "video_id": job.video_id,
                "status": job.status,
                "progress": job.progress,
                "total_frames": job.total_frames,
                "processed_frames": job.processed_frames,
                "error_message": job.error_message,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            },
            message="Job status retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/jobs", response_model=Dict[str, Any])
async def list_jobs(
    video_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """List computer vision processing jobs with optional filtering."""
    try:
        query = db.query(VideoProcessingJob)
        
        if video_id:
            query = query.filter(VideoProcessingJob.video_id == video_id)
        
        if status:
            query = query.filter(VideoProcessingJob.status == status)
        
        jobs = query.offset(offset).limit(limit).all()
        total = query.count()
        
        job_data = []
        for job in jobs:
            job_data.append({
                "job_id": job.id,
                "video_id": job.video_id,
                "status": job.status,
                "progress": job.progress,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            })
        
        return ResponseModel.success(
            data={
                "jobs": job_data,
                "total": total,
                "limit": limit,
                "offset": offset
            },
            message="Jobs retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.post("/analyze-image", response_model=Dict[str, Any])
async def analyze_image(
    *,
    image: UploadFile = File(...),
    enable_court_detection: bool = Form(True),
    enable_player_detection: bool = Form(True),
    enable_team_classification: bool = Form(True),
    enable_ball_detection: bool = Form(True)
) -> Dict[str, Any]:
    """
    Analyze a single basketball image with computer vision.

    This endpoint provides real-time analysis of a basketball image including:
    - Court detection and feature recognition
    - Player detection and tracking
    - Team classification
    - Ball detection
    """
    try:
        logger.info(f"Starting image analysis for {image.filename}")

        # Save uploaded image to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            import cv2
            import numpy as np

            # Load image
            frame = cv2.imread(temp_path)
            if frame is None:
                raise HTTPException(status_code=400, detail="Invalid image format")

            analysis_results = {}

            # Court detection with CNN-first approach
            if enable_court_detection:
                logger.info("Starting CNN-first court detection")
                court_detector = SimplifiedCourtDetector()
                court_features = court_detector.detect_court(frame)

                # Log the results for debugging
                logger.info(f"Court detection results: confidence={court_features.confidence_score:.3f}, "
                           f"method={court_features.detection_method}, "
                           f"corners={len(court_features.court_corners) if court_features.court_corners is not None else 0}")

                # Convert to API response format
                analysis_results['court_detection'] = court_features.to_dict()

            # Player detection
            if enable_player_detection:
                player_detector = PlayerDetector()
                players = player_detector.detect_players(frame, 0)
                analysis_results['player_detection'] = {
                    'player_count': len(players),
                    'players': [
                        {
                            'player_id': p.player_id,
                            'bbox': p.bbox,
                            'confidence': p.confidence,
                            'jersey_number': p.jersey_number
                        } for p in players
                    ]
                }

            # Team classification
            if enable_team_classification and enable_player_detection:
                team_classifier = TeamClassifier()
                if len(players) >= 3:  # Need minimum players for classification
                    player_data = [{'player_id': p.player_id, 'bbox': p.bbox} for p in players]
                    team_classification = team_classifier.classify_teams(frame, player_data)
                    analysis_results['team_classification'] = {
                        'team_a_players': team_classification.team_a_players,
                        'team_b_players': team_classification.team_b_players,
                        'classification_confidence': team_classification.classification_confidence,
                        'unclassified_players': team_classification.unclassified_players or [],
                        'team_a_colors': {
                            'primary_color': team_classification.team_a_colors.primary_color,
                            'secondary_color': team_classification.team_a_colors.secondary_color,
                            'color_name': team_classification.team_a_colors.color_name,
                            'confidence': team_classification.team_a_colors.confidence
                        },
                        'team_b_colors': {
                            'primary_color': team_classification.team_b_colors.primary_color,
                            'secondary_color': team_classification.team_b_colors.secondary_color,
                            'color_name': team_classification.team_b_colors.color_name,
                            'confidence': team_classification.team_b_colors.confidence
                        }
                    }
                else:
                    analysis_results['team_classification'] = {
                        'message': 'Insufficient players for team classification (minimum 4 required)'
                    }

            # Ball detection
            if enable_ball_detection:
                ball_detector = BallDetector()
                ball_detection = ball_detector.detect_ball(frame, 0)
                analysis_results['ball_detection'] = {
                    'ball_detected': ball_detection.position is not None,
                    'ball_position': ball_detection.position,
                    'confidence': ball_detection.confidence
                }

            # Convert numpy types to Python native types for JSON serialization
            analysis_results = convert_numpy_types(analysis_results)

            return ResponseModel.success(
                data=analysis_results,
                message="Image analysis completed successfully"
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze image: {str(e)}")


@router.post("/analyze-image-visual")
async def analyze_image_visual(
    *,
    image: UploadFile = File(...),
    enable_court_detection: bool = Form(True),
    enable_player_detection: bool = Form(True),
    enable_team_classification: bool = Form(True),
    enable_ball_detection: bool = Form(True)
):
    """
    Analyze a basketball image and return the image with visual annotations.

    This endpoint provides the same analysis as /analyze-image but returns
    the image with detected features highlighted and annotated.
    """
    try:
        logger.info(f"Starting visual image analysis for {image.filename}")

        # Save uploaded image to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await image.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            import cv2
            import numpy as np
            import io

            # Load image
            frame = cv2.imread(temp_path)
            if frame is None:
                raise HTTPException(status_code=400, detail="Invalid image format")

            # Create a copy for visualization
            vis_frame = frame.copy()

            # CNN-first court detection with visualization
            if enable_court_detection:
                court_detector = SimplifiedCourtDetector()
                court_features = court_detector.detect_court(frame)
                vis_frame = court_detector.draw_court_features(vis_frame, court_features)

            # Player detection with visualization
            if enable_player_detection:
                player_detector = PlayerDetector()
                players = player_detector.detect_players(frame, 0)
                vis_frame = _draw_player_detections(vis_frame, players)

            # Team classification with visualization
            if enable_team_classification and enable_player_detection:
                team_classifier = TeamClassifier()
                if len(players) >= 3:  # Need minimum players for classification
                    player_data = [{'player_id': p.player_id, 'bbox': p.bbox} for p in players]
                    team_classification = team_classifier.classify_teams(frame, player_data)

                    # Update player team assignments
                    for player in players:
                        if player.player_id in team_classification.team_a_players:
                            player.team_id = 'team_a'
                            player.team_confidence = team_classification.classification_confidence
                        elif player.player_id in team_classification.team_b_players:
                            player.team_id = 'team_b'
                            player.team_confidence = team_classification.classification_confidence
                        else:
                            player.team_id = 'unknown'
                            player.team_confidence = 0.0

                vis_frame = _draw_team_classifications(vis_frame, players)

            # Ball detection with visualization
            if enable_ball_detection:
                ball_detector = BallDetector()
                ball_detection = ball_detector.detect_ball(frame, 0)
                vis_frame = _draw_ball_detection(vis_frame, ball_detection)

            # Convert the annotated image to bytes
            _, buffer = cv2.imencode('.jpg', vis_frame)
            image_bytes = io.BytesIO(buffer.tobytes())

            return StreamingResponse(
                image_bytes,
                media_type="image/jpeg",
                headers={"Content-Disposition": "inline; filename=analyzed_image.jpg"}
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in visual image analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze image: {str(e)}")


@router.post("/analyze-image-progressive")
async def analyze_image_progressive(
    *,
    image: UploadFile = File(...),
    enable_court_detection: bool = Form(True),
    enable_player_detection: bool = Form(True),
    enable_team_classification: bool = Form(True),
    enable_ball_detection: bool = Form(True)
):
    """
    Analyze a basketball image with real-time progress updates via Server-Sent Events.

    This endpoint provides progressive analysis with live updates including:
    - Progress percentage
    - Intermediate results as they become available
    - Final annotated image
    """
    import asyncio
    import json
    import base64

    async def generate_progress():
        try:
            logger.info(f"Starting progressive image analysis for {image.filename}")

            # Save uploaded image to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                content = await image.read()
                temp_file.write(content)
                temp_path = temp_file.name

            try:
                import cv2
                import numpy as np
                import io

                # Load image
                frame = cv2.imread(temp_path)
                if frame is None:
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": "Invalid image format"})
                    }
                    return

                # Create a copy for visualization
                vis_frame = frame.copy()
                analysis_results = {}
                total_steps = sum([enable_court_detection, enable_player_detection,
                                 enable_team_classification, enable_ball_detection])
                current_step = 0

                # Send initial progress
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "percentage": 0,
                        "step": "Starting analysis...",
                        "total_steps": total_steps
                    })
                }

                await asyncio.sleep(0.1)  # Allow client to receive

                # Court detection with enhanced progress tracking
                if enable_court_detection:
                    current_step += 1

                    # Progress tracking for court detection
                    def court_progress_callback(percentage, step_name):
                        """Callback for court detection progress - this will be handled by the main generator"""
                        pass  # We'll handle progress updates in the main flow

                    court_detector = SimplifiedCourtDetector()
                    # Use CNN-first detection with progress tracking
                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "percentage": int((current_step / total_steps) * 25),
                            "step": "Detecting court features with enhanced algorithms...",
                            "current_step": current_step,
                            "total_steps": total_steps
                        })
                    }

                    court_features = court_detector.detect_court(frame, progress_callback=court_progress_callback)
                    vis_frame = court_detector.draw_court_features(vis_frame, court_features)

                    # Convert to API response format
                    analysis_results['court_detection'] = court_features.to_dict()

                    # Send intermediate result
                    yield {
                        "event": "intermediate",
                        "data": json.dumps({
                            "type": "court_detection",
                            "message": f"Court detected with {court_features.confidence_score:.1%} confidence",
                            "confidence": court_features.confidence_score,
                            "method": court_features.detection_method
                        })
                    }

                    # Send intermediate result
                    yield {
                        "event": "intermediate_result",
                        "data": json.dumps({
                            "type": "court_detection",
                            "result": analysis_results['court_detection'],
                            "message": f"Court detected with {court_features.confidence_score:.2f} confidence"
                        })
                    }

                    await asyncio.sleep(0.1)

                # Player detection with progress
                if enable_player_detection:
                    current_step += 1
                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "percentage": int((current_step / total_steps) * 50),
                            "step": "Detecting players...",
                            "current_step": current_step,
                            "total_steps": total_steps
                        })
                    }

                    player_detector = PlayerDetector()
                    players = player_detector.detect_players(frame, 0)
                    vis_frame = _draw_player_detections(vis_frame, players)

                    analysis_results['player_detection'] = {
                        'player_count': len(players),
                        'players': [
                            {
                                'player_id': p.player_id,
                                'confidence': p.confidence,
                                'bbox': p.bbox,
                                'jersey_number': getattr(p, 'jersey_number', None)
                            } for p in players
                        ]
                    }

                    # Send intermediate result
                    yield {
                        "event": "intermediate_result",
                        "data": json.dumps({
                            "type": "player_detection",
                            "result": analysis_results['player_detection'],
                            "message": f"Found {len(players)} players"
                        })
                    }

                    await asyncio.sleep(0.1)

                # Team classification with progress
                if enable_team_classification and enable_player_detection:
                    current_step += 1
                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "percentage": int((current_step / total_steps) * 75),
                            "step": "Classifying teams...",
                            "current_step": current_step,
                            "total_steps": total_steps
                        })
                    }

                    team_classifier = TeamClassifier()
                    if len(players) >= 3:  # Need minimum players for classification
                        player_data = [{'player_id': p.player_id, 'bbox': p.bbox} for p in players]
                        team_classification = team_classifier.classify_teams(frame, player_data)

                        # Update player team assignments
                        for player in players:
                            if player.player_id in team_classification.team_a_players:
                                player.team_id = 'team_a'
                                player.team_confidence = team_classification.classification_confidence
                            elif player.player_id in team_classification.team_b_players:
                                player.team_id = 'team_b'
                                player.team_confidence = team_classification.classification_confidence
                            else:
                                player.team_id = 'unknown'
                                player.team_confidence = 0.0

                    vis_frame = _draw_team_classifications(vis_frame, players)

                    team_counts = {}
                    for player in players:
                        team_id = getattr(player, 'team_id', 'unknown')
                        team_counts[team_id] = team_counts.get(team_id, 0) + 1

                    analysis_results['team_classification'] = {
                        'team_counts': team_counts,
                        'players_classified': len([p for p in players if hasattr(p, 'team_id')])
                    }

                    # Send intermediate result
                    yield {
                        "event": "intermediate_result",
                        "data": json.dumps({
                            "type": "team_classification",
                            "result": analysis_results['team_classification'],
                            "message": f"Classified {len(players)} players into teams"
                        })
                    }

                    await asyncio.sleep(0.1)

                # Ball detection with progress
                if enable_ball_detection:
                    current_step += 1
                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "percentage": int((current_step / total_steps) * 90),
                            "step": "Detecting ball...",
                            "current_step": current_step,
                            "total_steps": total_steps
                        })
                    }

                    ball_detector = BallDetector()
                    ball_detection = ball_detector.detect_ball(frame, 0)
                    vis_frame = _draw_ball_detection(vis_frame, ball_detection)

                    analysis_results['ball_detection'] = {
                        'ball_detected': ball_detection.position is not None,
                        'ball_position': ball_detection.position,
                        'confidence': ball_detection.confidence
                    }

                    # Send intermediate result
                    yield {
                        "event": "intermediate_result",
                        "data": json.dumps({
                            "type": "ball_detection",
                            "result": analysis_results['ball_detection'],
                            "message": "Ball detected" if ball_detection.detected else "No ball detected"
                        })
                    }

                    await asyncio.sleep(0.1)

                # Final processing
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "percentage": 95,
                        "step": "Finalizing results...",
                        "current_step": total_steps,
                        "total_steps": total_steps
                    })
                }

                # Convert the annotated image to base64
                _, buffer = cv2.imencode('.jpg', vis_frame)
                image_base64 = base64.b64encode(buffer).decode('utf-8')

                # Send final result
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "percentage": 100,
                        "analysis_results": analysis_results,
                        "annotated_image": f"data:image/jpeg;base64,{image_base64}",
                        "message": "Analysis completed successfully"
                    })
                }

            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"Error in progressive image analysis: {str(e)}")
            yield {
                "event": "error",
                "data": json.dumps({"error": f"Analysis failed: {str(e)}"})
            }

    return EventSourceResponse(generate_progress())


@router.get("/results/{job_id}", response_model=Dict[str, Any])
async def get_analysis_results(
    job_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed analysis results for a completed computer vision job."""
    try:
        job = db.query(VideoProcessingJob).filter(VideoProcessingJob.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status != "completed":
            raise HTTPException(status_code=400, detail="Job not completed yet")

        # Get analysis results from database
        from app.models.computer_vision import (
            CourtDetection, PlayerDetection, TeamClassification,
            BallDetection, GameStatistics
        )

        results = {}

        # Court detection results
        court_detections = db.query(CourtDetection).filter(
            CourtDetection.job_id == job_id
        ).all()
        results['court_detections'] = len(court_detections)

        # Player detection results
        player_detections = db.query(PlayerDetection).filter(
            PlayerDetection.job_id == job_id
        ).all()
        results['total_player_detections'] = len(player_detections)

        # Team classification results
        team_classifications = db.query(TeamClassification).filter(
            TeamClassification.job_id == job_id
        ).all()
        results['team_classifications'] = len(team_classifications)

        # Ball detection results
        ball_detections = db.query(BallDetection).filter(
            BallDetection.job_id == job_id
        ).all()
        results['ball_detections'] = len(ball_detections)

        # Game statistics
        game_stats = db.query(GameStatistics).filter(
            GameStatistics.job_id == job_id
        ).first()

        if game_stats:
            results['game_statistics'] = {
                'total_players_detected': game_stats.total_players_detected,
                'average_players_per_frame': game_stats.average_players_per_frame,
                'team_balance_score': game_stats.team_balance_score,
                'court_coverage_percentage': game_stats.court_coverage_percentage
            }

        return ResponseModel.success(
            data={
                "job_id": job_id,
                "video_id": job.video_id,
                "analysis_results": results,
                "processing_time_seconds": job.processing_time_seconds,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            },
            message="Analysis results retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


async def _get_video_data(video_id: int) -> Optional[Dict[str, Any]]:
    """Get video data from the main backend service."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://backend:8000/api/videos/{video_id}",
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json().get("data")
            else:
                logger.error(f"Failed to get video data: {response.status_code}")
                return None

    except Exception as e:
        logger.error(f"Error fetching video data: {str(e)}")
        return None


def _draw_court_features(frame, court_features):
    """Draw court detection features on the frame."""
    import cv2
    import numpy as np

    if not court_features or court_features.confidence_score < 0.1:
        return frame

    # Draw court corners
    if court_features.corners and len(court_features.corners) >= 4:
        corners = np.array(court_features.corners, dtype=np.int32)
        cv2.polylines(frame, [corners], True, (0, 255, 0), 3)  # Green court boundary

        # Draw corner points
        for i, corner in enumerate(corners):
            cv2.circle(frame, tuple(corner), 8, (0, 255, 0), -1)
            cv2.putText(frame, f'C{i+1}', (corner[0]+10, corner[1]-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# Removed _draw_enhanced_court_features - now using SimplifiedCourtDetector.draw_court_features

    # Draw center circle
    if court_features.center_circle:
        center = court_features.center_circle.get('center', [0, 0])
        radius = court_features.center_circle.get('radius', 0)
        if center and radius > 0:
            cv2.circle(frame, (int(center[0]), int(center[1])), int(radius), (255, 255, 0), 2)  # Cyan circle

    # Add confidence score
    cv2.putText(frame, f'Court: {court_features.confidence_score:.2f}',
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    return frame


def _draw_player_detections(frame, players):
    """Draw player detection bounding boxes on the frame."""
    import cv2

    for i, player in enumerate(players):
        if player.bbox:
            x1, y1, x2, y2 = map(int, player.bbox)

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 2)  # Magenta box

            # Draw player ID and confidence
            label = f'P{player.player_id}'
            if hasattr(player, 'confidence'):
                label += f' ({player.confidence:.2f})'

            cv2.putText(frame, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

            # Draw jersey number if available
            if hasattr(player, 'jersey_number') and player.jersey_number:
                cv2.putText(frame, f'#{player.jersey_number}',
                           (x1, y2+20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Add player count
    cv2.putText(frame, f'Players: {len(players)}',
               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

    return frame


def _draw_team_classifications(frame, players):
    """Draw team classification colors on player bounding boxes."""
    import cv2

    team_colors = {
        'team_1': (0, 0, 255),    # Red
        'team_2': (255, 0, 0),    # Blue
        'referee': (128, 128, 128), # Gray
        'unknown': (255, 255, 255)  # White
    }

    for player in players:
        if player.bbox and hasattr(player, 'team_id') and player.team_id:
            x1, y1, x2, y2 = map(int, player.bbox)

            # Get team color
            color = team_colors.get(player.team_id, team_colors['unknown'])

            # Draw colored border
            cv2.rectangle(frame, (x1-2, y1-2), (x2+2, y2+2), color, 4)

            # Draw team label
            team_label = player.team_id.replace('_', ' ').title()
            if hasattr(player, 'team_confidence'):
                team_label += f' ({player.team_confidence:.2f})'

            cv2.putText(frame, team_label, (x1, y2+40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    return frame


def _draw_ball_detection(frame, ball_detection):
    """Draw ball detection on the frame."""
    import cv2

    if ball_detection.detected and ball_detection.position:
        x, y = map(int, ball_detection.position)

        # Draw ball circle
        cv2.circle(frame, (x, y), 15, (0, 165, 255), 3)  # Orange circle
        cv2.circle(frame, (x, y), 3, (0, 165, 255), -1)  # Orange center dot

        # Draw confidence
        cv2.putText(frame, f'Ball: {ball_detection.confidence:.2f}',
                   (x+20, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        # Draw velocity if available
        if hasattr(ball_detection, 'velocity') and ball_detection.velocity:
            vx, vy = ball_detection.velocity
            # Draw velocity vector
            end_x = int(x + vx * 5)  # Scale velocity for visibility
            end_y = int(y + vy * 5)
            cv2.arrowedLine(frame, (x, y), (end_x, end_y), (0, 255, 255), 2)

    # Add ball status
    status = "Ball: Detected" if ball_detection.detected else "Ball: Not detected"
    cv2.putText(frame, status, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)

    return frame
