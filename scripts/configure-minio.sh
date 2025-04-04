#!/bin/bash

# Wait for MinIO to start
echo "Waiting for MinIO to start..."
sleep 10

# Configure MinIO CORS settings
echo "Configuring MinIO CORS settings..."
mc alias set myminio http://minio:9000 minioadmin minioadmin

# Configure CORS for the videos bucket
mc admin config set myminio cors <<EOF
{
  "corsRules": [
    {
      "allowedOrigins": ["*"],
      "allowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "allowedHeaders": ["*"],
      "exposeHeaders": ["ETag", "Content-Length", "Content-Type"],
      "maxAgeSeconds": 3600
    }
  ]
}
EOF

# Create the videos bucket if it doesn't exist
mc mb --ignore-existing myminio/videos

# Set public read policy for the videos bucket
mc policy set download myminio/videos

echo "MinIO configuration completed."
