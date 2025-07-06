"""
Video processing job manager for basketball analytics.

This module provides job queue management, batch processing, and
distributed processing capabilities for video analysis tasks.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from pathlib import Path

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.computer_vision import VideoProcessingJob
from ..processors.video_processor import VideoProcessor, VideoProcessingConfig, FrameAnalysis

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingJob:
    """Data class for video processing job."""
    job_id: str
    video_id: int
    video_path: str
    config: VideoProcessingConfig
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    results: Optional[List[FrameAnalysis]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class VideoProcessingJobManager:
    """
    Manages video processing jobs with queue management and batch processing.
    
    This class provides:
    - Job queue management
    - Concurrent processing
    - Progress tracking
    - Error handling and retry logic
    - Database persistence
    """
    
    def __init__(self, max_concurrent_jobs: int = 2, max_retries: int = 3):
        """
        Initialize the job manager.
        
        Args:
            max_concurrent_jobs: Maximum number of concurrent processing jobs
            max_retries: Maximum number of retry attempts for failed jobs
        """
        self.max_concurrent_jobs = max_concurrent_jobs
        self.max_retries = max_retries
        
        # Job management
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.active_jobs: Dict[str, ProcessingJob] = {}
        self.completed_jobs: Dict[str, ProcessingJob] = {}
        self.failed_jobs: Dict[str, ProcessingJob] = {}
        
        # Processing workers
        self.workers: List[asyncio.Task] = []
        self.is_running = False
        
        # Callbacks
        self.progress_callbacks: Dict[str, Callable] = {}
        self.completion_callbacks: Dict[str, Callable] = {}
        
        logger.info(f"VideoProcessingJobManager initialized with {max_concurrent_jobs} workers")
    
    async def start(self):
        """Start the job manager and processing workers."""
        if self.is_running:
            logger.warning("Job manager is already running")
            return
        
        self.is_running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent_jobs):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Job manager started with {len(self.workers)} workers")
    
    async def stop(self):
        """Stop the job manager and all workers."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Job manager stopped")
    
    async def submit_job(self, video_id: int, video_path: str, 
                        config: Optional[VideoProcessingConfig] = None,
                        progress_callback: Optional[Callable] = None,
                        completion_callback: Optional[Callable] = None) -> str:
        """
        Submit a video processing job.
        
        Args:
            video_id: Video ID from the main service
            video_path: Path to the video file
            config: Processing configuration
            progress_callback: Optional progress callback function
            completion_callback: Optional completion callback function
            
        Returns:
            Job ID string
        """
        try:
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            
            # Create job
            job = ProcessingJob(
                job_id=job_id,
                video_id=video_id,
                video_path=video_path,
                config=config or VideoProcessingConfig()
            )
            
            # Store callbacks
            if progress_callback:
                self.progress_callbacks[job_id] = progress_callback
            if completion_callback:
                self.completion_callbacks[job_id] = completion_callback
            
            # Save job to database
            await self._save_job_to_db(job)
            
            # Add to queue
            await self.job_queue.put(job)
            
            logger.info(f"Job {job_id} submitted for video {video_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Error submitting job: {str(e)}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status and progress.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status dictionary or None if job not found
        """
        # Check active jobs
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return self._job_to_dict(job)
        
        # Check completed jobs
        if job_id in self.completed_jobs:
            job = self.completed_jobs[job_id]
            return self._job_to_dict(job)
        
        # Check failed jobs
        if job_id in self.failed_jobs:
            job = self.failed_jobs[job_id]
            return self._job_to_dict(job)
        
        # Check database
        try:
            db = SessionLocal()
            db_job = db.query(VideoProcessingJob).filter(VideoProcessingJob.id == job_id).first()
            if db_job:
                return {
                    'job_id': str(db_job.id),
                    'video_id': db_job.video_id,
                    'status': db_job.status,
                    'progress': db_job.progress,
                    'created_at': db_job.created_at.isoformat() if db_job.created_at else None,
                    'started_at': db_job.started_at.isoformat() if db_job.started_at else None,
                    'completed_at': db_job.completed_at.isoformat() if db_job.completed_at else None,
                    'error_message': db_job.error_message,
                    'retry_count': db_job.retry_count
                }
            db.close()
        except Exception as e:
            logger.error(f"Error querying job status from database: {str(e)}")
        
        return None
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if job was cancelled, False otherwise
        """
        try:
            # Check if job is active
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                job.status = JobStatus.CANCELLED
                
                # Update database
                await self._update_job_in_db(job)
                
                logger.info(f"Job {job_id} cancelled")
                return True
            
            # Check if job is in queue (this is more complex and would require queue modification)
            # For now, we'll just mark it as cancelled in the database
            db = SessionLocal()
            db_job = db.query(VideoProcessingJob).filter(VideoProcessingJob.id == job_id).first()
            if db_job and db_job.status == JobStatus.QUEUED.value:
                db_job.status = JobStatus.CANCELLED.value
                db.commit()
                db.close()
                logger.info(f"Job {job_id} cancelled in database")
                return True
            
            db.close()
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {str(e)}")
            return False
    
    async def _worker(self, worker_name: str):
        """
        Worker coroutine that processes jobs from the queue.
        
        Args:
            worker_name: Name of the worker for logging
        """
        logger.info(f"Worker {worker_name} started")
        
        while self.is_running:
            try:
                # Get job from queue with timeout
                job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                
                # Check if job was cancelled
                if job.status == JobStatus.CANCELLED:
                    continue
                
                # Process the job
                await self._process_job(job, worker_name)
                
            except asyncio.TimeoutError:
                # No job available, continue
                continue
            except asyncio.CancelledError:
                # Worker was cancelled
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {str(e)}")
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _process_job(self, job: ProcessingJob, worker_name: str):
        """
        Process a single job.
        
        Args:
            job: Job to process
            worker_name: Name of the processing worker
        """
        try:
            logger.info(f"Worker {worker_name} processing job {job.job_id}")
            
            # Update job status
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now()
            self.active_jobs[job.job_id] = job
            
            # Update database
            await self._update_job_in_db(job)
            
            # Create video processor
            processor = VideoProcessor(job.config)
            
            # Define progress callback
            async def progress_callback(progress: float, analysis: FrameAnalysis):
                job.progress = progress
                await self._update_job_in_db(job)
                
                # Call user-defined progress callback
                if job.job_id in self.progress_callbacks:
                    try:
                        await self.progress_callbacks[job.job_id](progress, analysis)
                    except Exception as e:
                        logger.error(f"Error in progress callback: {str(e)}")
            
            # Process video
            results = await processor.process_video_file(job.video_path, progress_callback)
            
            # Job completed successfully
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress = 100.0
            job.results = results
            
            # Move to completed jobs
            self.completed_jobs[job.job_id] = job
            if job.job_id in self.active_jobs:
                del self.active_jobs[job.job_id]
            
            # Update database
            await self._update_job_in_db(job)
            
            # Call completion callback
            if job.job_id in self.completion_callbacks:
                try:
                    await self.completion_callbacks[job.job_id](job)
                except Exception as e:
                    logger.error(f"Error in completion callback: {str(e)}")
            
            logger.info(f"Job {job.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing job {job.job_id}: {str(e)}")
            
            # Handle job failure
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.retry_count += 1
            
            # Move to failed jobs or retry
            if job.retry_count <= self.max_retries:
                logger.info(f"Retrying job {job.job_id} (attempt {job.retry_count})")
                job.status = JobStatus.QUEUED
                await self.job_queue.put(job)
            else:
                logger.error(f"Job {job.job_id} failed after {job.retry_count} attempts")
                self.failed_jobs[job.job_id] = job
                if job.job_id in self.active_jobs:
                    del self.active_jobs[job.job_id]
            
            # Update database
            await self._update_job_in_db(job)

    async def _save_job_to_db(self, job: ProcessingJob):
        """Save job to database."""
        try:
            db = SessionLocal()

            db_job = VideoProcessingJob(
                id=job.job_id,
                video_id=job.video_id,
                status=job.status.value,
                progress=job.progress,
                processing_config=asdict(job.config),
                retry_count=job.retry_count,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                error_message=job.error_message
            )

            db.add(db_job)
            db.commit()
            db.close()

        except Exception as e:
            logger.error(f"Error saving job to database: {str(e)}")

    async def _update_job_in_db(self, job: ProcessingJob):
        """Update job in database."""
        try:
            db = SessionLocal()

            db_job = db.query(VideoProcessingJob).filter(VideoProcessingJob.id == job.job_id).first()
            if db_job:
                db_job.status = job.status.value
                db_job.progress = job.progress
                db_job.retry_count = job.retry_count
                db_job.started_at = job.started_at
                db_job.completed_at = job.completed_at
                db_job.error_message = job.error_message

                db.commit()

            db.close()

        except Exception as e:
            logger.error(f"Error updating job in database: {str(e)}")

    def _job_to_dict(self, job: ProcessingJob) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            'job_id': job.job_id,
            'video_id': job.video_id,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error_message': job.error_message,
            'retry_count': job.retry_count,
            'config': asdict(job.config)
        }


# Global job manager instance
job_manager = VideoProcessingJobManager()


async def start_job_manager():
    """Start the global job manager."""
    await job_manager.start()


async def stop_job_manager():
    """Stop the global job manager."""
    await job_manager.stop()


def get_job_manager() -> VideoProcessingJobManager:
    """Get the global job manager instance."""
    return job_manager
