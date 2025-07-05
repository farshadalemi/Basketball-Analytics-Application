# Docker Setup Guide

## Overview

This Basketball Analytics Application uses a simplified Docker architecture with:
- **One Dockerfile per service** (frontend, backend, scouting-service)
- **One docker-compose.yml** file for the entire application
- **CPU-only ML packages** for the scouting service
- **Optimized multi-stage builds** for smaller images

## Architecture

```
Basketball-Analytics-Application/
├── docker-compose.yml              # Single compose file
├── frontend/
│   └── Dockerfile                  # Multi-stage: dev + production
├── backend/
│   └── Dockerfile                  # Optimized Python service
├── scouting-service/
│   └── Dockerfile                  # CPU-only ML packages
└── scripts/
    └── init-multiple-databases.sh  # Database initialization
```

## Services

### 1. Frontend Service
- **Base**: Node.js 18 Alpine
- **Stages**: Development and Production
- **Port**: 3000
- **Features**: Hot-reload in development, optimized production build

### 2. Backend Service
- **Base**: Python 3.12 Slim
- **Port**: 8000
- **Features**: FastAPI, PostgreSQL, MinIO integration
- **Security**: Non-root user, health checks

### 3. Scouting Service
- **Base**: Python 3.12 Slim
- **Port**: 8001
- **Features**: CPU-only PyTorch, OpenCV, Computer Vision
- **Optimization**: Multi-stage build, CPU-only packages

### 4. Database Service
- **Image**: PostgreSQL 15 Alpine
- **Port**: 5432
- **Features**: Multiple database initialization, health checks

### 5. Storage Service
- **Image**: MinIO Latest
- **Ports**: 9000 (API), 9001 (Console)
- **Features**: Automatic bucket setup, CORS configuration

## Key Features

### CPU-Only ML Stack
The scouting service uses CPU-only versions of ML packages:
- PyTorch (CPU-only index)
- No CUDA dependencies
- Faster builds and smaller images
- Sufficient for development and testing

### Multi-Stage Builds
All Dockerfiles use multi-stage builds:
- Separate dependency installation stage
- Smaller final images
- Better caching
- Security improvements

### Health Checks
All services include health checks:
- Proper startup orchestration
- Dependency management
- Service reliability

### Security
- Non-root users in containers
- Minimal base images (Alpine/Slim)
- Proper file permissions
- Network isolation

## Quick Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild specific service
docker-compose build scouting-service

# Scale services (if needed)
docker-compose up -d --scale backend=2

# Stop and clean up
docker-compose down -v
```

## Environment Variables

Key environment variables are configured in docker-compose.yml:
- Database connections
- MinIO credentials
- Service URLs
- CPU optimization settings

## Troubleshooting

### Build Issues
```bash
# Clean build
docker-compose build --no-cache

# Remove old images
docker system prune -a
```

### Service Dependencies
Services start in proper order using health checks:
1. Database and MinIO first
2. Backend services after database is ready
3. Frontend after backend services are healthy

### Resource Requirements
- **Minimum**: 4GB RAM, 10GB disk space
- **Recommended**: 8GB RAM, 20GB disk space
- **CPU**: Multi-core recommended for ML processing
