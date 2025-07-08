"""
Analysis Job repository
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.analysis_job import AnalysisJob
from app.schemas.analysis_job import AnalysisJobCreate, AnalysisJobUpdate
from app.repositories.base_repository import BaseRepository


class AnalysisJobRepository(BaseRepository[AnalysisJob, AnalysisJobCreate, AnalysisJobUpdate]):
    """Repository for analysis job operations"""

    def get_by_job_id(self, db: Session, job_id: str) -> Optional[AnalysisJob]:
        """Get analysis job by job_id"""
        return db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()

    def get_by_video_id(self, db: Session, video_id: int) -> List[AnalysisJob]:
        """Get all analysis jobs for a video"""
        return db.query(AnalysisJob).filter(AnalysisJob.video_id == video_id).order_by(desc(AnalysisJob.created_at)).all()

    def get_by_user_id(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[AnalysisJob]:
        """Get all analysis jobs for a user"""
        return db.query(AnalysisJob).filter(AnalysisJob.user_id == user_id).order_by(desc(AnalysisJob.created_at)).offset(skip).limit(limit).all()

    def get_latest_by_video_id(self, db: Session, video_id: int) -> Optional[AnalysisJob]:
        """Get the latest analysis job for a video"""
        return db.query(AnalysisJob).filter(AnalysisJob.video_id == video_id).order_by(desc(AnalysisJob.created_at)).first()

    def create_with_user(self, db: Session, obj_in: AnalysisJobCreate, user_id: int) -> AnalysisJob:
        """Create analysis job with user_id"""
        obj_in_data = obj_in.dict()
        obj_in_data["user_id"] = user_id
        db_obj = AnalysisJob(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_active_jobs(self, db: Session) -> List[AnalysisJob]:
        """Get all active (pending or running) analysis jobs"""
        return db.query(AnalysisJob).filter(AnalysisJob.status.in_(["pending", "running"])).all()


# Create singleton instance
analysis_job_repository = AnalysisJobRepository(AnalysisJob)
