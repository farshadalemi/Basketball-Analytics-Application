import os
import sys
from sqlalchemy import create_engine, inspect
from app.core.config import settings

def test_migrations():
    """Test database migrations by checking if tables and columns exist."""
    print("Testing database migrations...")
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    # Check if tables exist
    tables = inspector.get_table_names()
    print(f"Tables in database: {tables}")
    
    if 'users' not in tables:
        print("ERROR: 'users' table does not exist!")
        return False
    
    if 'videos' not in tables:
        print("ERROR: 'videos' table does not exist!")
        return False
    
    # Check if columns exist in videos table
    columns = [col['name'] for col in inspector.get_columns('videos')]
    print(f"Columns in 'videos' table: {columns}")
    
    required_columns = [
        'id', 'title', 'description', 'file_path', 'content_type', 'user_id',
        'created_at', 'updated_at', 'processing_status', 'duration', 
        'thumbnail_url', 'processed_at'
    ]
    
    for col in required_columns:
        if col not in columns:
            print(f"ERROR: '{col}' column does not exist in 'videos' table!")
            return False
    
    print("All tables and columns exist. Migrations successful!")
    return True

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    test_migrations()
