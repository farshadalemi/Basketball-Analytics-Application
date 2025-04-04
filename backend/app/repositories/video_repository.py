"""Video repository module."""
from typing import List

from sqlalchemy.orm import Session

from app.models.video import Video
from app.repositories.base_repository import BaseRepository
from app.schemas.video import VideoCreate, VideoUpdate


class VideoRepository(BaseRepository[Video, VideoCreate, VideoUpdate]):
    """Video repository for video-specific operations."""

    def get_multi_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Video]:
        """Get multiple videos belonging to a user."""
        return (
            db.query(self.model)
            .filter(Video.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def create_with_owner(
        self, db: Session, *, obj_in: VideoCreate, user_id: int
    ) -> Video:
        """Create a new video with owner."""
        db_obj = Video(
            **obj_in.dict(),
            user_id=user_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


# Create a singleton instance
video_repository = VideoRepository(Video) 