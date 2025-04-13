#!/bin/bash
set -e

echo "Setting up database for scouting service..."

# Run Alembic migrations
alembic upgrade head

# Initialize database
python -m app.db.init_db

echo "Database setup completed!"
