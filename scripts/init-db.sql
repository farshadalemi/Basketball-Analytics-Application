-- Initialize databases for the Basketball Analytics Application
-- This script creates the necessary databases for both the main backend and scouting service

-- Create the main video database (if it doesn't exist)
SELECT 'CREATE DATABASE videodb'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'videodb')\gexec

-- Create the scouting database (if it doesn't exist)  
SELECT 'CREATE DATABASE scoutingdb'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'scoutingdb')\gexec

-- Grant permissions to postgres user for both databases
GRANT ALL PRIVILEGES ON DATABASE videodb TO postgres;
GRANT ALL PRIVILEGES ON DATABASE scoutingdb TO postgres;
