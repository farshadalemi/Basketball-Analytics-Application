"""Video service module."""
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.video import Video
from app.repositories.video_repository import video_repository
from app.schemas.video import VideoCreate, VideoUpdate
from app.services.minio_service import minio_service
from fastapi import UploadFile, HTTPException, status


class VideoService:
    """Video service for handling video operations."""

    def get_videos(
        self, db: Session, user: User, skip: int = 0, limit: int = 100
    ) -> List[Video]:
        """Get videos for a user."""
        if user.is_admin:
            return video_repository.get_multi(db=db, skip=skip, limit=limit)
        return video_repository.get_multi_by_user(
            db=db, user_id=user.id, skip=skip, limit=limit
        )

    def get_all_videos(
        self, db: Session, skip: int = 0, limit: int = 100, user_id: Optional[int] = None, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all videos with filtering options (admin only)."""
        query = db.query(Video)

        # Apply filters
        if user_id is not None:
            query = query.filter(Video.user_id == user_id)

        if status is not None:
            query = query.filter(Video.processing_status == status)

        # Apply pagination
        videos = query.offset(skip).limit(limit).all()

        # Format videos with user information
        result = []
        for video in videos:
            # Get user information
            user = db.query(User).filter(User.id == video.user_id).first()
            username = user.username if user else "Unknown"

            # Generate streaming URL
            streaming_url = minio_service.get_presigned_url(video.file_path)

            # Format datetime fields
            created_at = video.created_at.isoformat() if video.created_at else None
            updated_at = video.updated_at.isoformat() if video.updated_at else None
            processed_at = video.processed_at.isoformat() if video.processed_at else None

            result.append({
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "user_id": video.user_id,
                "username": username,
                "processing_status": video.processing_status,
                "content_type": video.content_type,
                "file_path": video.file_path,
                "thumbnail_url": video.thumbnail_url,
                "streaming_url": streaming_url,
                "duration": video.duration,
                "created_at": created_at,
                "updated_at": updated_at,
                "processed_at": processed_at
            })

        return result

    def get_video_by_id(self, db: Session, video_id: int) -> Video:
        """Get a video by ID (admin only)."""
        video = video_repository.get(db=db, id=video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        return video

    def get_video(
        self, db: Session, video_id: int, user: User
    ) -> Dict[str, Any]:
        """Get a video by ID with streaming URL."""
        print(f"[DEBUG] Getting video with ID: {video_id} for user: {user.id}")

        try:
            # Get video from database
            video = video_repository.get(db=db, id=video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found",
                )

            # Check permissions
            if video.user_id != user.id and not user.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                )

            # Print video details for debugging
            print(f"[DEBUG] Video found: {video.id}, title: {video.title}, duration: {video.duration}, type: {type(video.duration)}")

            # Generate presigned URL for streaming
            streaming_url = minio_service.get_presigned_url(video.file_path)
            if not streaming_url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate streaming URL",
                )

            # Create a safe serializable dictionary
            video_data = {
                "id": video.id,
                "title": video.title,
                "description": video.description or "",
                "content_type": video.content_type,
                "file_path": video.file_path,
                "user_id": video.user_id,
                "processing_status": video.processing_status or "unknown",
                "streaming_url": streaming_url,

                # Handle potentially problematic fields with safe defaults
                "duration": 0,  # Default duration
                "thumbnail_url": None,
                "created_at": None,
                "updated_at": None,
                "processed_at": None
            }

            # Safely handle datetime objects
            try:
                if video.created_at:
                    if hasattr(video.created_at, 'isoformat'):
                        video_data["created_at"] = video.created_at.isoformat()
                    else:
                        video_data["created_at"] = str(video.created_at)
            except Exception as e:
                print(f"[DEBUG] Error formatting created_at: {e}")

            try:
                if video.updated_at:
                    if hasattr(video.updated_at, 'isoformat'):
                        video_data["updated_at"] = video.updated_at.isoformat()
                    else:
                        video_data["updated_at"] = str(video.updated_at)
            except Exception as e:
                print(f"[DEBUG] Error formatting updated_at: {e}")

            try:
                if video.processed_at:
                    if hasattr(video.processed_at, 'isoformat'):
                        video_data["processed_at"] = video.processed_at.isoformat()
                    else:
                        video_data["processed_at"] = str(video.processed_at)
            except Exception as e:
                print(f"[DEBUG] Error formatting processed_at: {e}")

            # Safely handle duration
            try:
                if video.duration is not None:
                    video_data["duration"] = int(video.duration)
            except (ValueError, TypeError) as e:
                print(f"[DEBUG] Error converting duration: {e}, value: {video.duration}, type: {type(video.duration)}")
                video_data["duration"] = 0

            # Safely handle thumbnail URL
            if video.thumbnail_url:
                video_data["thumbnail_url"] = video.thumbnail_url

            print(f"[DEBUG] Returning video data: {video_data}")
            return video_data
        except Exception as e:
            print(f"Error serializing video data: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error serializing video data: {str(e)}"
            )

    def upload_video(
        self, db: Session, title: str, description: Optional[str], file: UploadFile, user: User
    ) -> Video:
        """Upload a new video."""
        try:
            # Validate file existence and name
            if not file or not hasattr(file, "file") or not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid file provided",
                )

            # Check file size (max 2GB = 2 * 1024 * 1024 * 1024 bytes)
            MAX_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

            if hasattr(file, "file"):
                position = file.file.tell()
                file.file.seek(0, 2)  # Move to end
                file_size = file.file.tell()
                file.file.seek(position)  # Reset position

                print(f"[VIDEO UPLOAD] File size: {file_size} bytes")

                if file_size == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="The uploaded file is empty"
                    )

                if file_size > MAX_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File size ({file_size} bytes) exceeds maximum allowed size (2GB)"
                    )

                # Check file extension
                allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.webm', '.flv', '.m4v', '.3gp', '.ts', '.mts']
                file_ext = '.' + file.filename.split('.')[-1].lower()

                print(f"[VIDEO UPLOAD] File extension: {file_ext}")

                if file_ext not in allowed_extensions:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}",
                    )

            # Validate file type
            content_type = file.content_type
            print(f"File content type: {content_type}")

            # Allow more types of videos or skip this check
            if not content_type or (not content_type.startswith("video/") and not content_type.startswith("application/")):
                print(f"Warning: File may not be a video. Content type: {content_type}")

            # Generate a unique filename
            filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
            object_name = f"{user.id}/{filename}"

            print(f"Uploading to MinIO: {object_name}")
            # Upload to MinIO
            upload_success = minio_service.upload_video(file, object_name, content_type or "video/mp4")
            if not upload_success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to upload video to storage",
                )

            print(f"Creating database entry for video: {title}")
            # Create DB entry
            video_in = VideoCreate(
                title=title,
                description=description or "",
                file_path=object_name,
                content_type=content_type or "video/mp4",
            )
            video = video_repository.create_with_owner(db=db, obj_in=video_in, user_id=user.id)
            return video

        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Error in upload_video: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Video upload failed: {str(e)}",
            )

    def delete_video(self, db: Session, video_id: int, user: User) -> Video:
        """Delete a video."""
        video = video_repository.get(db=db, id=video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )
        if video.user_id != user.id and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        # Delete from MinIO
        delete_success = minio_service.delete_video(video.file_path)
        if not delete_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete video file",
            )

        # Delete from DB
        video = video_repository.remove(db=db, id=video_id)
        return video

    def delete_video_admin(self, db: Session, video_id: int) -> bool:
        """Delete a video (admin only)."""
        video = video_repository.get(db=db, id=video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found",
            )

        # Delete from MinIO
        delete_success = minio_service.delete_video(video.file_path)
        if not delete_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete video file",
            )

        # Delete from DB
        video_repository.remove(db=db, id=video_id)
        return True

    def process_video_metadata(self, db: Session, video_id: int) -> None:
        """
        Process video metadata in the background.
        This method is called asynchronously after the video upload.
        """
        try:
            print(f"[VIDEO METADATA] Started processing for video_id={video_id}")

            # Get the video record
            video = video_repository.get(db=db, id=video_id)
            if not video:
                print(f"[VIDEO METADATA] Error: Video not found with id={video_id}")
                return

            # Update processing status
            video_update = VideoUpdate(processing_status="processing")
            video_repository.update(db=db, db_obj=video, obj_in=video_update)

            # Here we would typically extract metadata like:
            # - Video duration
            # - Resolution
            # - Codec information
            # - Generate thumbnails
            # For now, we'll just simulate processing with a delay
            import time
            time.sleep(5)  # Simulate processing time

            # Set thumbnail URL to the video URL for now (no thumbnail generation)
            thumbnail_url = None
            try:
                # Use a direct URL to the video as the thumbnail
                thumbnail_url = minio_service.get_direct_url(video.file_path)
                print(f"[VIDEO METADATA] Using direct video URL as thumbnail: {thumbnail_url}")
            except Exception as e:
                print(f"[VIDEO METADATA] Failed to set thumbnail URL: {str(e)}")

            # Set a random duration between 30 and 300 seconds for demo purposes
            import random
            random_duration = random.randint(30, 300)

            # Update the video with metadata
            video_update = VideoUpdate(
                processing_status="completed",
                duration=random_duration,  # Random duration for demo
                thumbnail_url=thumbnail_url,
                processed_at=datetime.now()
            )

            updated_video = video_repository.update(db=db, db_obj=video, obj_in=video_update)
            print(f"[VIDEO METADATA] Completed processing for video_id={video_id}")
            return updated_video

        except Exception as e:
            print(f"[VIDEO METADATA] Processing error for video_id={video_id}: {str(e)}")

            try:
                # Update status to failed
                video = video_repository.get(db=db, id=video_id)
                if video:
                    video_update = VideoUpdate(processing_status="failed")
                    video_repository.update(db=db, db_obj=video, obj_in=video_update)
            except Exception as update_error:
                print(f"[VIDEO METADATA] Failed to update processing status: {str(update_error)}")

            import traceback
            traceback.print_exc()


    def generate_thumbnail(self, video_path: str, thumbnail_path: str) -> str:
        """
        Generate a thumbnail from a video and upload it to MinIO.
        Note: This is a simplified version that doesn't use ffmpeg.

        Args:
            video_path: Path to the video in MinIO
            thumbnail_path: Path to save the thumbnail in MinIO

        Returns:
            URL to the thumbnail
        """

        # Since we don't have ffmpeg, we'll just return a direct URL to the video
        # In a real implementation, we would generate a thumbnail from the video
        try:
            # Just return a direct URL to the video
            direct_url = minio_service.get_direct_url(video_path)
            print(f"[THUMBNAIL] Using video URL as thumbnail: {direct_url}")
            return direct_url
        except Exception as e:
            print(f"[THUMBNAIL] Error generating thumbnail: {str(e)}")
            return None


# Create a singleton instance
video_service = VideoService()
