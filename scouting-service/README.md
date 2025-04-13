# Basketball Scouting Report Microservice

A microservice for generating scouting reports from basketball game videos.

## Features

- Process opponent game videos
- Detect and track players
- Analyze player movements and statistics
- Generate PDF scouting reports
- Integrate with the main basketball analytics platform

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Storage**: MinIO (for reports)
- **Computer Vision**: OpenCV, NumPy
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
  - `utils/`: Utility functions
- `alembic/`: Database migrations
- `scripts/`: Utility scripts

### Running Tests

```
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
