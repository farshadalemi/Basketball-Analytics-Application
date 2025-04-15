# Basketball Scouting Report Microservice

A microservice for generating scouting reports from basketball game videos.

## Features

- Process opponent game videos (supports full 40-minute games)
- Advanced player detection and tracking using YOLOv8
- Ball tracking and shot detection
- Court detection and mapping
- Team defense analysis with pose estimation
- Shot chart generation with zone analysis
- Player movement analysis and heatmaps
- Play type detection and analysis
- Advanced metrics calculation
- Comprehensive PDF scouting reports
- Integrate with the main basketball analytics platform

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Storage**: MinIO (for reports and videos)
- **Computer Vision**: OpenCV, YOLOv8, MediaPipe
- **Machine Learning**: NumPy, SciPy, scikit-learn
- **PDF Generation**: ReportLab, WeasyPrint
- **Containerization**: Docker

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
    - `video_analysis_service.py`: Video processing and analysis
    - `pdf_generator_service.py`: PDF report generation
  - `utils/`: Utility functions
    - `video_chunker.py`: Video chunking for large files
    - `player_detector.py`: Player detection and tracking
    - `ball_detector.py`: Ball detection and shot tracking
    - `court_detector.py`: Court detection and mapping
    - `team_defense_analysis.py`: Team defense analysis
    - `pose_estimation.py`: Player pose estimation
- `alembic/`: Database migrations
- `scripts/`: Utility scripts
- `tests/`: Test files
  - `data/`: Sample data for testing

### Sample Data

To test the service with sample data, place a basketball video file in the `tests/data` directory with the name `sample_basketball.mp4`.

### Running Tests

```
pytest
```

### Troubleshooting

#### Database Connection Issues

If you encounter database connection issues, make sure:

1. The PostgreSQL service is running
2. The database credentials are correct in the environment variables
3. The PostgreSQL client is installed in the container

#### Video Processing Issues

If video processing fails:

1. Check that OpenCV is properly installed
2. Ensure the video format is supported (MP4 recommended)
3. Check the logs for specific error messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.
