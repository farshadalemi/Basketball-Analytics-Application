# Basketball Scouting Report Microservice

A microservice for generating scouting reports from basketball game videos using advanced computer vision and analytics.

## Features

### Computer Vision
- **Court Detection**: Advanced basketball court detection with CNN-based algorithms and traditional CV methods
- **Player Tracking**: Multi-object player detection and tracking with team classification
- **Ball Detection**: Basketball detection and shot analysis with trajectory tracking
- **Video Processing**: Comprehensive video analysis with job management and performance monitoring

### Analytics & Reporting
- Process opponent game videos with real-time analysis
- Detect and track players with advanced movement analysis
- Analyze player movements, statistics, and performance metrics
- Generate comprehensive PDF scouting reports
- Integrate seamlessly with the main basketball analytics platform

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Storage**: MinIO (for reports)
- **Computer Vision**: OpenCV, NumPy, PyTorch (CPU-only), YOLO
- **PDF Generation**: ReportLab, WeasyPrint
- **Containerization**: Docker

## Architecture

The service is organized using a feature-based architecture for better maintainability and scalability:

```
app/
├── services/
│   ├── court_detection/          # Basketball court detection
│   │   ├── detectors/            # Detection algorithms
│   │   ├── models/               # ML models and training
│   │   └── validation/           # Testing and validation
│   ├── player_tracking/          # Player detection and tracking
│   │   ├── detectors/            # Player detection algorithms
│   │   ├── analysis/             # Movement and performance analysis
│   │   └── classification/       # Team classification
│   ├── ball_detection/           # Ball detection and shot analysis
│   │   ├── detectors/            # Ball detection algorithms
│   │   └── analysis/             # Shot detection and analysis
│   ├── video_processing/         # Video processing and job management
│   │   ├── processors/           # Video processing algorithms
│   │   └── management/           # Job management and monitoring
│   └── analytics/                # Analytics and reporting
│       └── services/             # Report and analysis services
├── api/                          # REST API endpoints
├── core/                         # Core configuration and utilities
├── db/                           # Database models and session management
├── models/                       # Data models
└── schemas/                      # API schemas
```

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Running the Service

1. Start the service using Docker Compose:
   ```
   docker-compose up -d
   ```

2. The service will be available at `http://localhost:8001`

## API Endpoints

### Create a Report

```
POST /api/reports
```

Request body:
```json
{
  "title": "Scouting Report - Team X",
  "description": "Analysis of Team X's game against Team Y",
  "video_id": 123,
  "team_name": "Team X",
  "opponent_name": "Team Y",
  "user_id": 456
}
```

### Get Reports

```
GET /api/reports
```

### Get Report by ID

```
GET /api/reports/{report_id}
```

### Download Report PDF

```
GET /api/reports/{report_id}/download
```

### Delete Report

```
DELETE /api/reports/{report_id}
```

## Development

### Project Structure

- `app/`: Main application code
  - `api/`: API routes and dependencies
  - `core/`: Core functionality (config, security, etc.)
  - `db/`: Database models and session management
  - `models/`: SQLAlchemy models
  - `schemas/`: Pydantic schemas
  - `services/`: Business logic
  - `utils/`: Utility functions
- `alembic/`: Database migrations
- `scripts/`: Utility scripts

### Running Tests

```
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
