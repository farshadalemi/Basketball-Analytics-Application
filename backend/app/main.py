from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, videos, users, admin, direct_stream
from app.api.responses import ResponseModel
from app.core.config import settings
from app.core.events import EventType, event_bus
from app.core.logging import logger
from app.core.service_discovery import service_registry
from app.api.errors import add_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application."""
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode")

    # Register services
    logger.info("Registering services")
    service_registry.register_service(settings.SERVICE_NAME, settings.SERVICE_URL)

    # Publish startup event
    await event_bus.publish(EventType.SYSTEM_STARTUP)

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}")

    # Publish shutdown event
    await event_bus.publish(EventType.SYSTEM_SHUTDOWN)


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
app.include_router(auth.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(direct_stream.router, prefix="/api/direct")


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


@app.get("/services")
async def list_services():
    """List registered services."""
    return ResponseModel.success(
        data=service_registry.list_services(),
        message="Registered services",
    )