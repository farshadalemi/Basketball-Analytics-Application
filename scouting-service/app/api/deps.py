"""Dependencies module for API routes."""
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
