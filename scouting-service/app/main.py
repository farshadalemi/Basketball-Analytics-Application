"""
Scouting Report Microservice - Main Application
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import reports, computer_vision
from app.api.responses import ResponseModel
from app.core.config import settings
from app.core.logging import logger
from app.api.errors import add_error_handlers
from app.services.computer_vision import start_job_manager, stop_job_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode")

    # Start computer vision job manager
    logger.info("Starting computer vision job manager")
    await start_job_manager()

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}")

    # Stop computer vision job manager
    logger.info("Stopping computer vision job manager")
    await stop_job_manager()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add global error handlers
add_error_handlers(app)

# Include routers
app.include_router(reports.router, prefix="/api")
app.include_router(computer_vision.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return ResponseModel.success(
        data={
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        },
        message=f"Welcome to {settings.PROJECT_NAME} API",
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return ResponseModel.success(
        data={
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        },
        message="Service is healthy",
    )
