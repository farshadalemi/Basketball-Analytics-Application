import os
from enum import Enum
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Environment(str, Enum):
    """Environment enumeration."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class LogFormat(str, Enum):
    """Log format enumeration."""
    JSON = "json"
    TEXT = "text"


class Settings(BaseSettings):
    """Application settings."""
    # Environment
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True

    # Base
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Video Platform"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Video Platform API"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret_key_for_development_only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/videodb")

    # MinIO
    MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    MINIO_URL: str = os.getenv("MINIO_URL", "minio:9000")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "videos")

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: LogFormat = LogFormat.TEXT

    # Service Discovery
    SERVICE_NAME: str = "video-service"
    SERVICE_URL: str = "http://localhost:8000"

    # Microservices
    ANALYTICS_SERVICE_URL: Optional[str] = None

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def validate_environment(cls, v: str) -> Environment:
        """Validate environment."""
        if isinstance(v, Environment):
            return v
        if v.lower() not in [e.value for e in Environment]:
            raise ValueError(f"Invalid environment: {v}")
        return Environment(v.lower())

    @field_validator("LOG_FORMAT", mode="before")
    @classmethod
    def validate_log_format(cls, v: str) -> LogFormat:
        """Validate log format."""
        if isinstance(v, LogFormat):
            return v
        if v.lower() not in [f.value for f in LogFormat]:
            raise ValueError(f"Invalid log format: {v}")
        return LogFormat(v.lower())

    class Config:
        """Pydantic config."""
        case_sensitive = True
        env_file = ".env"

settings = Settings()