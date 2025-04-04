#!/bin/bash
set -e

echo "Waiting for database to be ready..."
python -c "
import time
import sys
import psycopg2

# Wait for the database to be ready
while True:
    try:
        conn = psycopg2.connect(
            dbname='videodb',
            user='postgres',
            password='postgres',
            host='db',
            port='5432'
        )
        conn.close()
        break
    except psycopg2.OperationalError:
        print('Database not ready yet. Waiting...')
        time.sleep(2)
"

echo "Database is ready!"

# Initialize database (run migrations and create admin user)
echo "Initializing database..."
python -m app.db.init_db

# Start the application
echo "Starting the application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload