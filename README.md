# Basketball Analytics Application

A comprehensive basketball analytics platform with video processing, player tracking, and automated scouting report generation. Built with React (frontend), FastAPI (backend services), PostgreSQL for database storage, and MinIO for file storage.

![Image](https://github.com/user-attachments/assets/f3b28047-14ab-4443-ad0b-01c9773229e2)

![Image](https://github.com/user-attachments/assets/658b69ca-5e27-492c-8df9-eac279572871)

## Features

### Core Platform
- User registration and authentication
- Upload and manage basketball game videos
- Stream videos with advanced controls
- User profiles and admin capabilities

### Basketball Analytics
- **Computer Vision**: Court detection, player tracking, ball tracking
- **Scouting Reports**: Automated generation of PDF scouting reports
- **Player Analysis**: Movement patterns, statistics, and performance metrics
- **Team Analytics**: Formation analysis, play pattern recognition
- **Real-time Processing**: Progress indicators for long-running analysis

## Architecture

The application consists of three main services:

1. **Frontend Service**: React-based user interface
2. **Backend Service**: Main API and video management
3. **Scouting Service**: Computer vision and analytics processing with CPU-only ML packages

## Tech Stack

- **Frontend**: React 18, Material-UI, Axios
- **Backend**: FastAPI (Python 3.12), SQLAlchemy, Alembic
- **Scouting Service**: FastAPI, OpenCV, PyTorch (CPU-only), scikit-learn, NumPy
- **Database**: PostgreSQL 15
- **Storage**: MinIO (for videos and reports)
- **Containerization**: Docker and Docker Compose
- **Computer Vision**: OpenCV, PyTorch, YOLO, PaddleOCR

## Prerequisites

- Docker and Docker Compose installed on your machine
- At least 4GB RAM available for Docker containers
- 10GB free disk space for images and data

## Quick Start

1. **Clone this repository**
   ```bash
   git clone <repository-url>
   cd Basketball-Analytics-Application
   ```

2. **Start all services with a single command**
   ```bash
   docker-compose up -d
   ```

   This will start all services:
   - Frontend (React development server)
   - Backend API
   - Scouting Service (with CPU-only ML packages)
   - PostgreSQL database
   - MinIO storage

3. **Access the application**
   - **Frontend**: [http://localhost:3000](http://localhost:3000)
   - **Backend API**: [http://localhost:8000](http://localhost:8000)
   - **Scouting API**: [http://localhost:8001](http://localhost:8001)
   - **MinIO Console**: [http://localhost:9001](http://localhost:9001) (login: minioadmin/minioadmin)
   - **Database**: localhost:5432 (postgres/postgres)

4. **Stop all services**
   ```bash
   docker-compose down
   ```

5. **Clean up (remove volumes)**
   ```bash
   docker-compose down -v
   ```

## Docker Architecture

The application uses a **single docker-compose.yml** file with optimized Dockerfiles:

### Service Structure
```
├── frontend/Dockerfile          # Multi-stage: development + production
├── backend/Dockerfile           # Optimized Python service
├── scouting-service/Dockerfile  # CPU-only ML packages
└── docker-compose.yml           # Single compose file for all services
```

### Key Optimizations
- **Multi-stage builds** for smaller final images
- **CPU-only PyTorch** for faster builds and smaller footprint
- **Health checks** for proper service orchestration
- **Non-root users** for security
- **Proper dependency management** with service conditions

## API Documentation

Once running, access the API documentation:
- **Main Backend**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Scouting Service**: [http://localhost:8001/docs](http://localhost:8001/docs)

## Development

### Local Development (without Docker)

#### Frontend
```bash
cd frontend
npm install
npm start  # Runs on http://localhost:3000
```

#### Backend
```bash
cd backend
pip install -r requirements.txt
python run.py  # Runs on http://localhost:8000
```

#### Scouting Service
```bash
cd scouting-service
pip install -r requirements-cpu.txt  # CPU-only packages
python run.py  # Runs on http://localhost:8001
```

### Docker Development

For development with hot-reload:
```bash
docker-compose up  # Without -d to see logs
```

The frontend uses development mode with hot-reload, and backend services mount source code as volumes.

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 3000, 8000, 8001, 5432, 9000, 9001 are available
2. **Memory issues**: Increase Docker memory limit to at least 4GB
3. **Build failures**: Try `docker-compose build --no-cache` to rebuild from scratch
4. **Database connection**: Wait for health checks to pass before accessing services

### Logs
```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs frontend
docker-compose logs backend
docker-compose logs scouting-service
```

### Reset Everything
```bash
# Stop and remove everything
docker-compose down -v --remove-orphans

# Remove all images
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

## CPU-Only ML Packages

The scouting service uses CPU-only versions of machine learning packages for:
- **Faster builds**: No CUDA dependencies
- **Smaller images**: Reduced container size
- **Better compatibility**: Works on any hardware
- **Development focus**: Sufficient for development and testing

Packages include:
- PyTorch (CPU-only)
- OpenCV
- scikit-learn
- NumPy/SciPy
- PaddleOCR
- YOLO models

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `docker-compose up`
5. Submit a pull request

## License

MIT
