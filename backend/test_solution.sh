#!/bin/bash
set -e

echo "Testing the migration fix..."

# Check if we're in a Docker container
if [ -f /.dockerenv ]; then
    echo "Running in Docker container"
    # Use the database URL from environment
    export DATABASE_URL=${DATABASE_URL:-"postgresql://postgres:postgres@db:5432/videodb"}
else
    echo "Running locally"
    # Use a local database URL
    export DATABASE_URL=${DATABASE_URL:-"postgresql://postgres:postgres@localhost:5432/videodb"}
fi

echo "Using DATABASE_URL: $DATABASE_URL"

# Reset the database (drop and recreate)
echo "Resetting the database..."
python -c "
import psycopg2
from urllib.parse import urlparse
import time

# Parse the DATABASE_URL
url = urlparse('$DATABASE_URL')
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

# Connect to postgres database to drop and recreate the target database
try:
    # Connect to postgres database
    conn = psycopg2.connect(
        dbname='postgres',
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Drop the database if it exists
    cursor.execute(f\"DROP DATABASE IF EXISTS {dbname}\")
    print(f'Dropped database {dbname}')
    
    # Create the database
    cursor.execute(f\"CREATE DATABASE {dbname}\")
    print(f'Created database {dbname}')
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f'Error resetting database: {e}')
    exit(1)
"

# Run the migrations
echo "Running migrations..."
python -m alembic upgrade head

# Test the migrations
echo "Testing migrations..."
python test_migrations.py

echo "Test completed!"
