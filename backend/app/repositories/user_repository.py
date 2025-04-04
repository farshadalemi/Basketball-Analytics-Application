"""User repository module."""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.base_repository import BaseRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """User repository for user-specific operations."""

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get a user by email."""
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """Get a user by username."""
        return db.query(User).filter(User.username == username).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user with hashed password."""
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            is_active=True,
            is_admin=False,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        print(f"Attempting to authenticate user with email: {email}")
        user = self.get_by_email(db, email=email)
        if not user:
            print(f"No user found with email: {email}")
            # Try username instead
            user = self.get_by_username(db, username=email)
            if not user:
                print(f"No user found with username: {email}")
                return None
            print(f"Found user with username: {email}")
        else:
            print(f"Found user with email: {email}")
        
        print(f"Stored hashed password: {user.hashed_password}")
        if not verify_password(password, user.hashed_password):
            print(f"Password verification failed for user: {email}")
            return None
        print(f"Password verification successful for user: {email}")
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active

    def is_admin(self, user: User) -> bool:
        """Check if user is admin."""
        return user.is_admin


# Create a singleton instance
user_repository = UserRepository(User) 