from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import io

from app.db.session import get_db
from app.services.auth_service import auth_service
from app.models.user import User
from app.services.video_service import video_service
from app.services.minio_service import minio_service

router = APIRouter()

@router.get("/videos/{video_id}")
async def direct_stream_video(
    video_id: int,
    self: bool = True,  # Make self parameter optional with default value True
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user),
):
    """
    Directly stream a video by ID without using presigned URLs.
    This endpoint reads the video data from MinIO and streams it directly to the client.
    """
    try:
        # Get the video
        video = video_service.get_video(db=db, video_id=video_id, user=current_user)
        if not video or not video.get("file_path"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found or file path not available"
            )

        # Get the file path from the video data
        file_path = video.get("file_path")

        # Get the video data from MinIO
        try:
            # Get the object data
            response = minio_service.get_object(file_path)
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video file not found"
                )

            # Read the entire file into memory
            data = response.read()
            response.close()  # Close the connection to MinIO

            # Determine content type
            content_type = video.get("content_type", "video/mp4")

            # Return the video as a response
            return Response(
                content=data,
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to stream video: {str(e)}"
            )
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error
        print(f"Error in direct_stream_video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stream video: {str(e)}"
        )
