"""Dependencies module for API routes."""
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.dependencies import get_db
from app.services.minio_service import minio_service


def get_minio_client():
    """
    Get MinIO client.
    """
    return minio_service.client
