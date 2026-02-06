"""
Main FastAPI application entry point for AppArt Agent.
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import analysis, documents, photos, properties, users, webhooks
from app.core.config import settings
from app.core.logging import instrument_fastapi, setup_logfire, setup_logging

# Initialize logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Initialize Logfire tracing
setup_logfire(
    service_name="appart-agent-backend", environment=settings.ENVIRONMENT, enable_console=True
)

# Create FastAPI app
app = FastAPI(
    title="AppArt Agent API",
    description="AI-powered apartment purchasing decision platform for France",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Instrument FastAPI app with Logfire
instrument_fastapi(app)

logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Storage backend: {settings.STORAGE_BACKEND}")

# Build CORS origins list
cors_origins = list(settings.ALLOWED_ORIGINS)
if settings.EXTRA_CORS_ORIGINS:
    cors_origins.extend([o.strip() for o in settings.EXTRA_CORS_ORIGINS.split(",") if o.strip()])

# In production, allow Cloud Run URLs
if settings.ENVIRONMENT == "production":
    cors_origins.append("https://*.run.app")

logger.info(f"CORS origins: {cors_origins}")

# CORS middleware with regex pattern support for Cloud Run
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.run\.app",  # Allow all Cloud Run URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist (with error handling for Cloud Run)
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")
except (PermissionError, OSError) as e:
    logger.warning(f"Could not create upload directory {settings.UPLOAD_DIR}: {e}")
    # Fall back to /tmp which is always writable in Cloud Run
    settings.UPLOAD_DIR = "/tmp/uploads"
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Using fallback upload directory: {settings.UPLOAD_DIR}")

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(properties.router, prefix="/api/properties", tags=["properties"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(photos.router, prefix="/api/photos", tags=["photos"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "Welcome to AppArt Agent API",
        "version": "1.0.0",
        "status": "active",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
