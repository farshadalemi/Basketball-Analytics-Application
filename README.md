# Video Platform App

A full-stack web application for uploading and streaming videos, built with React (frontend) and FastAPI (backend), using PostgreSQL for database storage and MinIO for video file storage.

## Features

- User registration and authentication
- Upload videos
- Stream videos
- Manage uploaded videos
- User profiles
- Admin capabilities

## Tech Stack

- **Frontend**: React, Material-UI
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Storage**: MinIO (for videos)
- **Containerization**: Docker and Docker Compose

## Prerequisites

- Docker and Docker Compose installed on your machine

## Running the Application

1. Clone this repository

2. Start the services using Docker Compose:
   ```
   docker-compose up -d
   ```

3. Access the application:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - MinIO Console: [http://localhost:9001](http://localhost:9001) (login with minioadmin/minioadmin)

4. Stop the services:
   ```
   docker-compose down
   ```

## API Documentation

Once the application is running, you can access the API documentation at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Development

### Frontend

To run the frontend in development mode:

```
cd frontend
npm install
npm start
```

### Backend

To run the backend in development mode:

```
cd backend
pip install -r requirements.txt
python run.py
```

## License

MIT 