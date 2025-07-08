"""
Configuration settings for the scouting service
"""
import os
from typing import List

class Settings:
    # Service configuration
    SERVICE_NAME: str = "scouting-service"
    SERVICE_URL: str = "http://localhost:8001"
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/scoutingdb")
    
    # MinIO configuration
    MINIO_URL: str = os.getenv("MINIO_URL", "localhost:9000")
    MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "videos")
    
    # Main backend URL
    MAIN_BACKEND_URL: str = os.getenv("MAIN_BACKEND_URL", "http://localhost:8000")
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://frontend:3000",
        "http://backend:8000"
    ]
    
    # File paths
    INPUT_VIDEOS_PATH: str = "input_videos"
    OUTPUT_VIDEOS_PATH: str = "output_videos"
    MODELS_PATH: str = "models"
    STUBS_PATH: str = "stubs"
    
    # Analysis settings
    MAX_CONCURRENT_JOBS: int = 2
    JOB_TIMEOUT_MINUTES: int = 60

settings = Settings()
