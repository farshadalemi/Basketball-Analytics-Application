#!/bin/bash
set -e

echo "Initializing database for scouting service..."

# Check if PostgreSQL client is installed
if ! command -v psql &> /dev/null; then
    echo "Error: PostgreSQL client is not installed. Please update the Dockerfile."
    exit 1
fi

echo "Checking if database exists..."
# Check if database exists, if not create it
if PGPASSWORD=postgres psql -h db -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'scoutingdb'" | grep -q 1; then
    echo "Database 'scoutingdb' already exists."
else
    echo "Creating database 'scoutingdb'..."
    PGPASSWORD=postgres psql -h db -U postgres -c "CREATE DATABASE scoutingdb;"
    echo "Database created successfully!"
fi

echo "Running database migrations..."
# Run migrations
cd /app
alembic upgrade head

echo "Database initialization completed!"
