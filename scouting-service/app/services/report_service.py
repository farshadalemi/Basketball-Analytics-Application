"""Report service for handling scouting reports."""
import os
import tempfile
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.report import Report
from app.schemas.report import ReportCreate, ReportUpdate, TeamAnalysis
from app.services.video_analysis_service import video_analysis_service
from app.services.pdf_generator_service import pdf_generator_service
from app.core.logging import logger


class ReportService:
    """Service for handling scouting reports."""
    
    def create_report(self, db: Session, report_in: ReportCreate) -> Report:
        """
        Create a new report in the database.
        
        Args:
            db: Database session
            report_in: Report creation data
            
        Returns:
            The created report
        """
        # Create report object
        db_report = Report(
            title=report_in.title,
            description=report_in.description,
            video_id=report_in.video_id,
            video_title=report_in.video_title,
            team_name=report_in.team_name,
            opponent_name=report_in.opponent_name,
            game_date=report_in.game_date,
            user_id=report_in.user_id,
            status="queued"
        )
        
        # Save to database
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        logger.info(f"Created report with ID: {db_report.id}")
        return db_report
    
    def get_reports(
        self, db: Session, user_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get reports, optionally filtered by user_id.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of reports
        """
        query = db.query(Report)
        
        if user_id is not None:
            query = query.filter(Report.user_id == user_id)
        
        reports = query.order_by(Report.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convert to dictionaries
        result = []
        for report in reports:
            result.append({
                "id": report.id,
                "title": report.title,
                "description": report.description,
                "video_id": report.video_id,
                "video_title": report.video_title,
                "team_name": report.team_name,
                "opponent_name": report.opponent_name,
                "game_date": report.game_date.isoformat() if report.game_date else None,
                "status": report.status,
                "user_id": report.user_id,
                "created_at": report.created_at.isoformat(),
                "updated_at": report.updated_at.isoformat(),
                "completed_at": report.completed_at.isoformat() if report.completed_at else None,
                "download_url": f"/api/reports/{report.id}/download" if report.status == "completed" else None
            })
        
        return result
    
    def get_report(self, db: Session, report_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a report by ID.
        
        Args:
            db: Database session
            report_id: Report ID
            
        Returns:
            The report or None if not found
        """
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return None
        
        # Convert to dictionary
        result = {
            "id": report.id,
            "title": report.title,
            "description": report.description,
            "video_id": report.video_id,
            "video_title": report.video_title,
            "team_name": report.team_name,
            "opponent_name": report.opponent_name,
            "game_date": report.game_date.isoformat() if report.game_date else None,
            "status": report.status,
            "user_id": report.user_id,
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat(),
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
            "analysis_results": report.analysis_results,
            "download_url": f"/api/reports/{report.id}/download" if report.status == "completed" else None
        }
        
        return result
    
    def update_report(self, db: Session, report_id: int, report_in: ReportUpdate) -> Optional[Report]:
        """
        Update a report.
        
        Args:
            db: Database session
            report_id: Report ID
            report_in: Report update data
            
        Returns:
            The updated report or None if not found
        """
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return None
        
        # Update fields
        update_data = report_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(report, field, value)
        
        db.commit()
        db.refresh(report)
        
        return report
    
    def delete_report(self, db: Session, report_id: int) -> bool:
        """
        Delete a report.
        
        Args:
            db: Database session
            report_id: Report ID
            
        Returns:
            True if deleted, False if not found
        """
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return False
        
        db.delete(report)
        db.commit()
        
        return True
    
    def get_report_file_path(self, db: Session, report_id: int) -> Optional[str]:
        """
        Get the file path for a report.
        
        Args:
            db: Database session
            report_id: Report ID
            
        Returns:
            The file path or None if not found
        """
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report or not report.file_path:
            return None
        
        return report.file_path
    
    async def generate_report(self, db: Session, report_id: int) -> None:
        """
        Generate a scouting report.
        
        This method is intended to be run as a background task.
        
        Args:
            db: Database session
            report_id: Report ID
        """
        logger.info(f"Starting report generation for report ID: {report_id}")
        
        # Get report
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            logger.error(f"Report not found: {report_id}")
            return
        
        try:
            # Update status to processing
            report.status = "processing"
            db.commit()
            
            # Get video data from main service
            logger.info(f"Fetching video data for video ID: {report.video_id}")
            video_data = await video_analysis_service.get_video_data(report.video_id)
            
            # Analyze video
            logger.info(f"Analyzing video: {report.video_id}")
            analysis_results = await video_analysis_service.analyze_video(video_data)
            
            # Generate PDF
            logger.info(f"Generating PDF for report: {report_id}")
            pdf_path = await pdf_generator_service.generate_pdf(analysis_results, report)
            
            # Update report with results
            report.status = "completed"
            report.file_path = pdf_path
            report.analysis_results = analysis_results
            report.completed_at = datetime.now()
            db.commit()
            
            logger.info(f"Report generation completed for report ID: {report_id}")
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            
            # Update status to failed
            report.status = "failed"
            db.commit()


# Create a singleton instance
report_service = ReportService()
