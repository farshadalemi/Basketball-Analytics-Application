"""Authentication service module."""
from datetime import timedelta
from typing import Optional, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.token import TokenPayload, Token
from app.schemas.user import UserCreate, User as UserSchema
from app.core.security import verify_password, get_password_hash

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthService:
    """Authentication service for login and token operations."""

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        return user_repository.authenticate(db=db, email=email, password=password)

    def create_access_token(self, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
        """Create an access token for a user."""
        if expires_delta:
            expire = expires_delta
        else:
            expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Pass is_admin to token claims
        user = user_repository.get(db=next(get_db()), id=user_id)
        is_admin = user.is_admin if user else False
        
        return create_access_token(
            subject=user_id,
            expires_delta=expire,
            is_admin=is_admin
        )

    def get_current_user(
        self, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
    ) -> User:
        """Get the current user from the token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
        except (JWTError, ValidationError):
            raise credentials_exception
        
        user = user_repository.get(db=db, id=token_data.sub)
        if not user:
            raise credentials_exception
        return user

    def get_current_active_user(
        self, current_user: User = Depends(get_current_user)
    ) -> User:
        """Get the current active user."""
        if not user_repository.is_active(current_user):
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

    def get_current_active_admin(
        self, current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Get the current active admin."""
        if not user_repository.is_admin(current_user):
            raise HTTPException(
                status_code=403, detail="The user doesn't have enough privileges"
            )
        return current_user
    
    def register_user(self, db: Session, user_in: UserCreate) -> User:
        """Register a new user."""
        # Validate password
        if len(user_in.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
            
        # Check if email exists
        user = user_repository.get_by_email(db=db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username exists
        user = user_repository.get_by_username(db=db, username=user_in.username)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create user
        user = user_repository.create(db=db, obj_in=user_in)
        return user
    
    def debug_admin(self, db: Session) -> dict[str, Any]:
        """Debug endpoint to check admin user."""
        admin = user_repository.get_by_username(db=db, username="admin")
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin user not found in database"
            )
        
        # Test password verification
        test_plain_password = "admin123"
        verification_result = verify_password(test_plain_password, admin.hashed_password)
        
        # Create a new hash for the same password
        new_hash = get_password_hash(test_plain_password)
        
        return {
            "status": "success",
            "admin_exists": True,
            "admin_id": admin.id,
            "admin_email": admin.email,
            "admin_username": admin.username,
            "admin_is_active": admin.is_active,
            "admin_is_admin": admin.is_admin,
            "admin_hashed_password": admin.hashed_password,
            "password_verification_result": verification_result,
            "generated_new_hash": new_hash
        }


# Create a singleton instance
auth_service = AuthService()
