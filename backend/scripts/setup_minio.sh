#!/bin/bash

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
sleep 10

# Set up MinIO client
mc alias set myminio http://minio:9000 minioadmin minioadmin

# Create bucket if it doesn't exist
mc mb --ignore-existing myminio/videos

# Set bucket policy to allow public read access
cat > /tmp/policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": ["*"]
      },
      "Action": [
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::videos/*"
      ]
    }
  ]
}
EOF

# Apply the policy
mc policy set-json /tmp/policy.json myminio/videos

# Set CORS configuration
cat > /tmp/cors.json << EOF
{
  "cors": [
    {
      "allowedHeaders": ["*"],
      "allowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "allowedOrigins": ["*"],
      "exposeHeaders": ["ETag", "Content-Length", "Content-Type"],
      "maxAgeSeconds": 3600
    }
  ]
}
EOF

# Apply CORS configuration
mc admin config set myminio cors:config /tmp/cors.json

# Restart MinIO to apply changes
mc admin service restart myminio

echo "MinIO setup completed successfully!"
