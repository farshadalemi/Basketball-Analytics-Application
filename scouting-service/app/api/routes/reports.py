"""Routes for scouting reports."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Path
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.responses import ResponseModel
from app.db.session import get_db
from app.schemas.report import Report, ReportCreate, ReportUpdate, TeamAnalysis
from app.services.report_service import report_service
from app.core.logging import logger

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/", response_model=Dict[str, Any])
async def create_report(
    *,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks,
    report_in: ReportCreate,
) -> Dict[str, Any]:
    """
    Create a new scouting report.
    
    This endpoint initiates the creation of a scouting report based on a video.
    The report generation happens asynchronously in the background.
    """
    logger.info(f"Creating report for video {report_in.video_id}")
    
    # Create report in database
    report = report_service.create_report(db=db, report_in=report_in)
    
    # Start report generation in background
    background_tasks.add_task(
        report_service.generate_report,
        db=db,
        report_id=report.id
    )
    
    return ResponseModel.success(
        data={"report_id": report.id, "status": report.status},
        message="Report creation initiated",
        status_code=status.HTTP_202_ACCEPTED,
    )


@router.get("/", response_model=Dict[str, Any])
async def list_reports(
    *,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> Dict[str, Any]:
    """
    List scouting reports.
    
    Optionally filter by user_id.
    """
    reports = report_service.get_reports(
        db=db, user_id=user_id, skip=skip, limit=limit
    )
    
    return ResponseModel.success(
        data=reports,
        message="Reports retrieved successfully",
    )


@router.get("/{report_id}", response_model=Dict[str, Any])
async def get_report(
    *,
    db: Session = Depends(get_db),
    report_id: int = Path(...),
) -> Dict[str, Any]:
    """
    Get a specific scouting report by ID.
    """
    report = report_service.get_report(db=db, report_id=report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    return ResponseModel.success(
        data=report,
        message="Report retrieved successfully",
    )


@router.get("/{report_id}/download")
async def download_report(
    *,
    db: Session = Depends(get_db),
    report_id: int = Path(...),
) -> FileResponse:
    """
    Download a report PDF.
    """
    report_path = report_service.get_report_file_path(db=db, report_id=report_id)
    if not report_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found",
        )
    
    return FileResponse(
        path=report_path,
        filename=f"scouting_report_{report_id}.pdf",
        media_type="application/pdf",
    )


@router.delete("/{report_id}", response_model=Dict[str, Any])
async def delete_report(
    *,
    db: Session = Depends(get_db),
    report_id: int = Path(...),
) -> Dict[str, Any]:
    """
    Delete a scouting report.
    """
    success = report_service.delete_report(db=db, report_id=report_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    return ResponseModel.success(
        message="Report deleted successfully",
    )
