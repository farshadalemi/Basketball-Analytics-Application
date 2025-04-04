"""User routes."""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate
from app.services.auth_service import auth_service
from app.services.user_service import user_service

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserSchema)
def read_user_me(
    self: bool = Query(None, description="Legacy parameter, not used"),
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    self: bool = Query(None, description="Legacy parameter, not used"),
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    try:
        return user_service.update_user(db=db, user_in=user_in, current_user=current_user)
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error
        print(f"Error updating user: {str(e)}")
        import traceback
        traceback.print_exc()

        # Raise HTTP exception with appropriate message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}"
        )

@router.get("/", response_model=List[UserSchema])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    _: User = Depends(auth_service.get_current_active_admin),  # Admin check
) -> Any:
    """
    Retrieve users. Admin only.
    """
    try:
        return user_service.get_users(db=db, skip=skip, limit=limit)
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error
        print(f"Error retrieving users: {str(e)}")
        import traceback
        traceback.print_exc()

        # Raise HTTP exception with appropriate message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )

@router.get("/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """
    Get a specific user by id.
    """
    try:
        return user_service.get_user_by_id(db=db, user_id=user_id, current_user=current_user)
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log the error
        print(f"Error retrieving user by ID: {str(e)}")
        import traceback
        traceback.print_exc()

        # Raise HTTP exception with appropriate message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )
