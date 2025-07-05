#!/bin/bash
set -e

# Initialize multiple databases for the Basketball Analytics Application
echo "Creating multiple databases..."

# Create databases if they don't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create videodb database (main backend database)
    SELECT 'CREATE DATABASE videodb'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'videodb')\gexec

    -- Create scoutingdb database (scouting service database)
    SELECT 'CREATE DATABASE scoutingdb'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'scoutingdb')\gexec

    -- Grant all privileges to postgres user
    GRANT ALL PRIVILEGES ON DATABASE videodb TO postgres;
    GRANT ALL PRIVILEGES ON DATABASE scoutingdb TO postgres;
EOSQL

echo "Multiple databases created successfully!"
