"""
Scouting routes - Integration with scouting service
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.services.auth_service import auth_service
from app.services.video_service import video_service
from app.services.scouting_service import scouting_service_client
from app.services.minio_service import minio_service
from app.repositories.analysis_job_repository import analysis_job_repository
from app.schemas.analysis_job import AnalysisJobCreate, AnalysisJobSchema

router = APIRouter(prefix="/scouting", tags=["scouting"])

@router.post("/analyze/{video_id}")
async def start_video_analysis(
    video_id: int,
    analysis_options: Optional[Dict] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Start basketball analysis for a video
    """
    try:
        # Get the video and verify ownership
        video_data = video_service.get_video(db=db, video_id=video_id, user=current_user)
        if not video_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        
        # Download video from MinIO to a temporary location for analysis
        # For now, we'll pass the MinIO path directly to the scouting service
        video_path = video_data["file_path"]
        
        # Start analysis job
        result = await scouting_service_client.start_analysis(
            video_id=video_id,
            video_path=video_path,
            analysis_options=analysis_options
        )

        # Save analysis job to database
        job_create = AnalysisJobCreate(
            job_id=result.get("job_id"),
            video_id=video_id,
            status=result.get("status", "pending"),
            analysis_options=str(analysis_options) if analysis_options else None
        )
        analysis_job_repository.create_with_user(db=db, obj_in=job_create, user_id=current_user.id)

        return {
            "message": "Analysis started successfully",
            "job_id": result.get("job_id"),
            "status": result.get("status"),
            "video_id": video_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {str(e)}"
        )

@router.get("/jobs/{job_id}/status")
async def get_analysis_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Get analysis job status
    """
    try:
        # First try to get status from scouting service
        status_data = await scouting_service_client.get_job_status(job_id)

        if status_data:
            return status_data

        # If not found in scouting service, check backend database
        db_job = analysis_job_repository.get_by_job_id(db=db, job_id=job_id)

        if db_job:
            # Check if this job belongs to the current user
            if db_job.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Analysis job not found"
                )

            # Return status from database (job might have been lost from scouting service)
            return {
                "job_id": db_job.job_id,
                "status": "failed",  # Mark as failed since it's not in scouting service
                "progress": db_job.progress or 0,
                "message": "Job was interrupted and needs to be restarted",
                "error": "Job lost from analysis service, possibly due to service restart"
            }

        # Job not found anywhere
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis job not found"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis status: {str(e)}"
        )

@router.get("/jobs/{job_id}/result")
async def get_analysis_result(
    job_id: str,
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Get analysis result download URL
    """
    try:
        # Check if job is completed
        status_data = await scouting_service_client.get_job_status(job_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis job not found"
            )
        
        if status_data.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Analysis not completed. Current status: {status_data.get('status')}"
            )
        
        # Get result URL
        result_url = await scouting_service_client.get_result_url(job_id)
        
        if not result_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis result not available"
            )
        
        return {
            "result_url": result_url,
            "job_id": job_id,
            "status": status_data.get("status")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis result: {str(e)}"
        )

@router.get("/jobs")
async def list_analysis_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    List all analysis jobs for current user
    """
    try:
        jobs = analysis_job_repository.get_by_user_id(db=db, user_id=current_user.id)
        # Convert to dictionaries for proper serialization
        job_dicts = []
        for job in jobs:
            job_dict = {
                "id": job.id,
                "job_id": job.job_id,
                "video_id": job.video_id,
                "user_id": job.user_id,
                "status": job.status,
                "progress": job.progress,
                "message": job.message,
                "error_message": job.error_message,
                "analysis_options": job.analysis_options,
                "result_url": job.result_url,
                "download_url": job.download_url,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            }
            job_dicts.append(job_dict)
        return {"jobs": job_dicts}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list analysis jobs: {str(e)}"
        )

@router.get("/videos/{video_id}/jobs")
async def get_video_analysis_jobs(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Get analysis jobs for a specific video
    """
    try:
        # Verify video ownership
        video_data = video_service.get_video(db=db, video_id=video_id, user=current_user)
        if not video_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )

        jobs = analysis_job_repository.get_by_video_id(db=db, video_id=video_id)
        # Convert to dictionaries for proper serialization
        job_dicts = []
        for job in jobs:
            job_dict = {
                "id": job.id,
                "job_id": job.job_id,
                "video_id": job.video_id,
                "user_id": job.user_id,
                "status": job.status,
                "progress": job.progress,
                "message": job.message,
                "error_message": job.error_message,
                "analysis_options": job.analysis_options,
                "result_url": job.result_url,
                "download_url": job.download_url,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            }
            job_dicts.append(job_dict)
        return {"jobs": job_dicts}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video analysis jobs: {str(e)}"
        )

@router.delete("/jobs/{job_id}")
async def delete_analysis_job(
    job_id: str,
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Delete analysis job and results
    """
    try:
        success = await scouting_service_client.delete_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis job not found"
            )
        
        return {"message": "Analysis job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete analysis job: {str(e)}"
        )

@router.post("/jobs/{job_id}/cleanup")
async def cleanup_stale_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Clean up a stale analysis job from the database
    """
    try:
        # Get the job from database
        db_job = analysis_job_repository.get_by_job_id(db=db, job_id=job_id)

        if not db_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis job not found"
            )

        # Check if this job belongs to the current user
        if db_job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis job not found"
            )

        # Check if job exists in scouting service
        status_data = await scouting_service_client.get_job_status(job_id)

        if status_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job is still active in scouting service"
            )

        # Remove the job from database
        db.delete(db_job)
        db.commit()

        return {"message": "Stale analysis job cleaned up successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup analysis job: {str(e)}"
        )

@router.get("/health")
async def scouting_service_health() -> Any:
    """
    Check scouting service health
    """
    try:
        is_healthy = await scouting_service_client.health_check()

        return {
            "scouting_service": "healthy" if is_healthy else "unhealthy",
            "status": "ok" if is_healthy else "error"
        }

    except Exception as e:
        return {
            "scouting_service": "unhealthy",
            "status": "error",
            "error": str(e)
        }
