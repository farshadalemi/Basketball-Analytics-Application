"""Database initialization module."""
import os
import sys
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base_class import Base
from app.models.report import Report


def create_tables(engine) -> None:
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def init_db() -> None:
    """Initialize the database with tables and initial data."""
    try:
        # Create engine and session
        print(f"Connecting to database: {settings.DATABASE_URL}")
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # Create tables
            create_tables(engine)
            print("Database initialization completed successfully!")
        finally:
            db.close()
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Add the current directory to the path so we can import app modules
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    init_db()
