"""Admin routes for system management."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.admin import SystemStats, UserStats, StorageStats
from app.services.auth_service import auth_service
from app.services.user_service import user_service
from app.services.video_service import video_service
from app.core.logging import logger

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    db: Session = Depends(get_db),
    _: User = Depends(auth_service.get_current_active_admin),  # Admin check
) -> Any:
    """
    Get system statistics.
    Admin only.
    """
    try:
        # User statistics
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
        admin_users = db.query(func.count(User.id)).filter(User.is_admin == True).scalar() or 0
        
        # Video statistics
        total_videos = db.query(func.count(Video.id)).scalar() or 0
        processing_videos = db.query(func.count(Video.id)).filter(
            Video.processing_status == "processing"
        ).scalar() or 0
        completed_videos = db.query(func.count(Video.id)).filter(
            Video.processing_status == "completed"
        ).scalar() or 0
        
        # Storage statistics
        # Note: This is an approximation, as we don't store file sizes directly
        # For a production system, you'd want to track actual file sizes
        avg_video_size_mb = 10  # Assumed average size in MB
        total_storage_mb = total_videos * avg_video_size_mb
        
        return {
            "user_stats": {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "admin_users": admin_users,
                "regular_users": total_users - admin_users
            },
            "video_stats": {
                "total_videos": total_videos,
                "processing_videos": processing_videos,
                "completed_videos": completed_videos,
                "failed_videos": total_videos - processing_videos - completed_videos
            },
            "storage_stats": {
                "total_storage_mb": total_storage_mb,
                "avg_storage_per_user_mb": total_storage_mb / total_users if total_users > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system statistics: {str(e)}"
        )


@router.get("/users/stats", response_model=UserStats)
async def get_user_stats(
    db: Session = Depends(get_db),
    _: User = Depends(auth_service.get_current_active_admin),  # Admin check
) -> Any:
    """
    Get detailed user statistics.
    Admin only.
    """
    try:
        total_users = db.query(func.count(User.id)).scalar() or 0
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
        admin_users = db.query(func.count(User.id)).filter(User.is_admin == True).scalar() or 0
        
        # Get users with most videos
        users_with_videos = (
            db.query(
                User.id,
                User.username,
                User.email,
                func.count(Video.id).label("video_count")
            )
            .outerjoin(Video, User.id == Video.user_id)
            .group_by(User.id)
            .order_by(func.count(Video.id).desc())
            .limit(5)
            .all()
        )
        
        top_users = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "video_count": user.video_count
            }
            for user in users_with_videos
        ]
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "admin_users": admin_users,
            "regular_users": total_users - admin_users,
            "top_users_by_content": top_users
        }
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user statistics: {str(e)}"
        )


@router.get("/storage/stats", response_model=StorageStats)
async def get_storage_stats(
    db: Session = Depends(get_db),
    _: User = Depends(auth_service.get_current_active_admin),  # Admin check
) -> Any:
    """
    Get detailed storage statistics.
    Admin only.
    """
    try:
        # Video statistics
        total_videos = db.query(func.count(Video.id)).scalar() or 0
        
        # Storage statistics (approximation)
        avg_video_size_mb = 10  # Assumed average size in MB
        total_storage_mb = total_videos * avg_video_size_mb
        
        # Get users with most storage
        users_with_storage = (
            db.query(
                User.id,
                User.username,
                User.email,
                func.count(Video.id).label("video_count")
            )
            .outerjoin(Video, User.id == Video.user_id)
            .group_by(User.id)
            .order_by(func.count(Video.id).desc())
            .limit(5)
            .all()
        )
        
        top_storage_users = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "video_count": user.video_count,
                "storage_used_mb": user.video_count * avg_video_size_mb
            }
            for user in users_with_storage
        ]
        
        return {
            "total_storage_mb": total_storage_mb,
            "total_videos": total_videos,
            "avg_video_size_mb": avg_video_size_mb,
            "top_storage_users": top_storage_users
        }
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage statistics: {str(e)}"
        )


@router.put("/users/{user_id}/activate", response_model=Dict[str, Any])
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(auth_service.get_current_active_admin),  # Admin check
) -> Any:
    """
    Activate a user.
    Admin only.
    """
    try:
        user = user_service.activate_user(db=db, user_id=user_id)
        return {
            "message": f"User {user.username} activated successfully",
            "user_id": user.id,
            "is_active": user.is_active
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error activating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}"
        )


@router.put("/users/{user_id}/deactivate", response_model=Dict[str, Any])
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(auth_service.get_current_active_admin),  # Admin check
) -> Any:
    """
    Deactivate a user.
    Admin only.
    """
    try:
        user = user_service.deactivate_user(db=db, user_id=user_id)
        return {
            "message": f"User {user.username} deactivated successfully",
            "user_id": user.id,
            "is_active": user.is_active
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deactivating user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )


@router.delete("/users/{user_id}", response_model=Dict[str, Any])
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(auth_service.get_current_active_admin),  # Admin check
) -> Any:
    """
    Delete a user and all their content.
    Admin only.
    """
    try:
        # Get user info before deletion for the response
        user = user_service.get_user_by_id(db=db, user_id=user_id, current_user=_)
        username = user.username
        
        # Delete the user
        user_service.delete_user(db=db, user_id=user_id)
        
        return {
            "message": f"User {username} deleted successfully",
            "user_id": user_id
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.get("/videos", response_model=List[Dict[str, Any]])
async def get_all_videos(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: int = Query(None),
    status: str = Query(None),
    _: User = Depends(auth_service.get_current_active_admin),  # Admin check
) -> Any:
    """
    Get all videos in the system with filtering options.
    Admin only.
    """
    try:
        return video_service.get_all_videos(
            db=db, 
            skip=skip, 
            limit=limit, 
            user_id=user_id, 
            status=status
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting videos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get videos: {str(e)}"
        )


@router.delete("/videos/{video_id}", response_model=Dict[str, Any])
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(auth_service.get_current_active_admin),  # Admin check
) -> Any:
    """
    Delete a video.
    Admin only.
    """
    try:
        # Get video info before deletion for the response
        video = video_service.get_video_by_id(db=db, video_id=video_id)
        title = video.title
        
        # Delete the video
        video_service.delete_video_admin(db=db, video_id=video_id)
        
        return {
            "message": f"Video '{title}' deleted successfully",
            "video_id": video_id
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting video: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete video: {str(e)}"
        )
