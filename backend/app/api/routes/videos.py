"""Video routes."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.video import Video as VideoSchema
from app.services.auth_service import auth_service
from app.services.video_service import video_service

router = APIRouter(prefix="/videos", tags=["videos"])

@router.get("/", response_model=List[VideoSchema])
def get_videos(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Retrieve videos for the current user.
    """
    try:
        return video_service.get_videos(db=db, user=current_user, skip=skip, limit=limit)
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error
        print(f"Error retrieving videos: {str(e)}")
        # Return a consistent error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve videos: {str(e)}"
        )

@router.post("/", response_model=VideoSchema)
def upload_video(
    db: Session = Depends(get_db),
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile = File(...),
    current_user: User = Depends(auth_service.get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> Any:
    """
    Upload new video.

    Accepts most common video formats with maximum size of 2GB.
    Supported formats: MP4, AVI, MOV, MKV, WMV, WEBM, FLV, etc.
    """
    try:
        # Log upload attempt
        print(f"[VIDEO UPLOAD] Started: user_id={current_user.id}, title={title}, filename={file.filename}")

        # Call the service to handle validation and upload
        video = video_service.upload_video(
            db=db, title=title, description=description, file=file, user=current_user
        )

        # Log success
        print(f"[VIDEO UPLOAD] Success: video_id={video.id}, path={video.file_path}")

        # Add metadata processing in the background
        background_tasks.add_task(
            video_service.process_video_metadata,
            db=db,
            video_id=video.id
        )

        return video
    except HTTPException as he:
        # Log HTTP exceptions
        print(f"[VIDEO UPLOAD] HTTP Exception: status={he.status_code}, detail={he.detail}")
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        # Log unexpected errors
        print(f"[VIDEO UPLOAD] Error: {str(e)}")
        import traceback
        traceback.print_exc()

        # Create user-friendly error message
        error_msg = str(e)
        user_message = "Failed to upload video"

        # Generate user-friendly messages for common errors
        if "MinIO" in error_msg or "S3Error" in error_msg:
            user_message = "Storage service unavailable. Please try again later."
        elif "database" in error_msg.lower():
            user_message = "Database error. Please try again later."
        elif "content_type" in error_msg.lower():
            user_message = "Invalid file format. Please upload a video file."

        # Raise HTTP exception with appropriate message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_message
        )

@router.get("/{video_id}", response_model=Dict[str, Any])
def get_video(
    *,
    db: Session = Depends(get_db),
    video_id: int,
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Get video by ID with streaming URL.
    """
    try:
        return video_service.get_video(db=db, video_id=video_id, user=current_user)
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        # Log the error
        print(f"Error retrieving video: {str(e)}")
        import traceback
        traceback.print_exc()

        # Raise HTTP exception with appropriate message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve video: {str(e)}"
        )

@router.delete("/{video_id}", response_model=VideoSchema)
def delete_video(
    *,
    db: Session = Depends(get_db),
    video_id: int,
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Delete video.
    """
    try:
        return video_service.delete_video(db=db, video_id=video_id, user=current_user)
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        # Log the error
        print(f"Error deleting video: {str(e)}")
        import traceback
        traceback.print_exc()

        # Raise HTTP exception with appropriate message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete video: {str(e)}"
        )

@router.get("/stream/{video_id}")
async def stream_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Stream a video by ID.
    """
    try:
        # Get the video
        video = video_service.get_video(db=db, video_id=video_id, user=current_user)
        if not video or not video.get("streaming_url"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found or streaming URL not available"
            )

        # Get the file path from the video data
        file_path = video.get("file_path")
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file path not found"
            )

        # Get the video directly from MinIO using the service
        from app.services.minio_service import minio_service

        # Get the object data directly from MinIO
        try:
            # Get the object data directly from MinIO
            response = minio_service.get_object(file_path)
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video file not found"
                )

            # Determine content type
            content_type = video.get("content_type", "video/mp4")

            # Return the video as a streaming response
            return StreamingResponse(
                content=response,
                media_type=content_type,
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": f"inline; filename={video.get('title', 'video')}.mp4",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        except Exception as e:
            print(f"Error streaming video: {str(e)}")

            # Try a different approach - return a direct URL
            try:
                # Create a direct URL to the video file
                direct_url = f"http://localhost:9000/videos/{file_path}"
                print(f"[DEBUG] Using direct URL: {direct_url}")

                # Return the direct URL
                return {"streaming_url": direct_url}
            except Exception as direct_url_error:
                print(f"Error creating direct URL: {str(direct_url_error)}")

                # Return a 500 error
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to stream video: {str(e)}"
                )
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error
        print(f"Error streaming video: {str(e)}")
        import traceback
        traceback.print_exc()

        # Raise HTTP exception with appropriate message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream video: {str(e)}"
        )
