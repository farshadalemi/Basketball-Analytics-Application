"""User service module."""
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import UserUpdate


class UserService:
    """User service for handling user operations."""

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users (admin only)."""
        return user_repository.get_multi(db=db, skip=skip, limit=limit)

    def get_user_by_id(self, db: Session, user_id: int, current_user: User) -> User:
        """Get a specific user by ID."""
        user = user_repository.get(db=db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check permissions - only allow access to own profile or admin access
        if user.id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this user profile"
            )

        return user

    def update_user(
        self, db: Session, user_in: UserUpdate, current_user: User
    ) -> User:
        """Update user information."""
        # Validate email if provided
        if user_in.email and user_in.email != current_user.email:
            existing_user = user_repository.get_by_email(db=db, email=user_in.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

        # Validate username if provided
        if user_in.username and user_in.username != current_user.username:
            existing_user = user_repository.get_by_username(db=db, username=user_in.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken",
                )

        # Validate password if provided
        if user_in.password and len(user_in.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long",
            )

        user = user_repository.update(db=db, db_obj=current_user, obj_in=user_in)
        return user

    def activate_user(self, db: Session, user_id: int) -> User:
        """Activate a user (admin only)."""
        user = user_repository.get(db=db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.is_active:
            return user  # Already active

        user_update = {"is_active": True}
        updated_user = user_repository.update(db=db, db_obj=user, obj_in=user_update)
        return updated_user

    def deactivate_user(self, db: Session, user_id: int) -> User:
        """Deactivate a user (admin only)."""
        user = user_repository.get(db=db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate admin users"
            )

        if not user.is_active:
            return user  # Already inactive

        user_update = {"is_active": False}
        updated_user = user_repository.update(db=db, db_obj=user, obj_in=user_update)
        return updated_user

    def delete_user(self, db: Session, user_id: int) -> bool:
        """Delete a user and all their content (admin only)."""
        user = user_repository.get(db=db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete admin users"
            )

        # Delete user's videos first
        from app.models.video import Video
        videos = db.query(Video).filter(Video.user_id == user_id).all()
        for video in videos:
            # Delete video file from storage
            from app.services.minio_service import minio_service
            try:
                minio_service.delete_file(video.file_path)
            except Exception as e:
                print(f"Error deleting video file: {str(e)}")

            # Delete video from database
            db.delete(video)

        # Delete the user
        db.delete(user)
        db.commit()

        return True


# Create a singleton instance
user_service = UserService()
