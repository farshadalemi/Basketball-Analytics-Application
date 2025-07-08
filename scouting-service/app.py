"""
FastAPI Web Service for Basketball Scouting Analysis
"""
import os
import uuid
import asyncio
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn

from analysis_service import AnalysisService
from models.database import init_db
from models.analysis_job import AnalysisJob, JobStatus
from config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Basketball Scouting Service",
    description="Advanced basketball video analysis service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analysis service
analysis_service = AnalysisService()

# Pydantic models for API
class AnalysisRequest(BaseModel):
    video_id: int
    video_path: str
    analysis_options: Optional[Dict] = {}

class AnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None
    result_path: Optional[str] = None
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    await init_db()
    
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Basketball Scouting Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "scouting-service"}

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_video(
    background_tasks: BackgroundTasks,
    video_id: int,
    video_path: str,
    analysis_options: Optional[Dict] = None
):
    """
    Start video analysis job
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create analysis job record
        job = AnalysisJob(
            job_id=job_id,
            video_id=video_id,
            video_path=video_path,
            status=JobStatus.PENDING,
            analysis_options=analysis_options or {}
        )
        
        # Save job to database (implement this)
        # await save_analysis_job(job)
        
        # Start analysis in background
        background_tasks.add_task(
            analysis_service.analyze_video,
            job_id,
            video_path,
            analysis_options or {}
        )
        
        return AnalysisResponse(
            job_id=job_id,
            status="started",
            message="Video analysis started"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {str(e)}"
        )

@app.get("/api/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get analysis job status
    """
    try:
        # Get job status from service
        job_status = await analysis_service.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
            
        return JobStatusResponse(**job_status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )

@app.get("/api/jobs/{job_id}/result")
async def get_analysis_result(job_id: str):
    """
    Get analysis result file
    """
    try:
        result_path = await analysis_service.get_result_path(job_id)
        
        if not result_path or not os.path.exists(result_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Result not found"
            )
            
        return FileResponse(
            path=result_path,
            media_type="video/mp4",
            filename=f"analysis_{job_id}.mp4"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get result: {str(e)}"
        )

@app.get("/api/jobs", response_model=List[JobStatusResponse])
async def list_jobs():
    """
    List all analysis jobs
    """
    try:
        jobs = await analysis_service.list_jobs()
        return [JobStatusResponse(**job) for job in jobs]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete analysis job and results
    """
    try:
        success = await analysis_service.delete_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
            
        return {"message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
