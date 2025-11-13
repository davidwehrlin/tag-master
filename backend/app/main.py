"""
FastAPI application entry point.

Creates and configures the FastAPI application with all middleware, routers, and lifecycle events.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import close_db, init_db
from app.middleware.cors import configure_cors
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.v1.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events for database and other resources.
    """
    # Startup: Initialize database (optional - use Alembic migrations in production)
    # await init_db()  # Uncomment for testing without migrations
    
    yield
    
    # Shutdown: Close database connections
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="Disc Golf Tag League API",
    description="REST API for managing disc golf tag leagues with dynamic rankings",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,  # Disable docs in production
    redoc_url="/redoc" if settings.is_development else None,
)

# Configure CORS
configure_cors(app)

# Add middleware (order matters - first added is outermost layer)
app.add_middleware(ErrorHandlerMiddleware)  # Catch all unhandled exceptions
app.add_middleware(LoggingMiddleware)  # Log all requests/responses
app.add_middleware(RateLimitMiddleware)  # Rate limiting per user

# Include routers
app.include_router(health_router, prefix="", tags=["health"])

# API v1 routers (Phase 3+)
from app.api.v1 import api_router
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Disc Golf Tag League API",
        "version": "1.0.0",
        "docs": "/docs" if settings.is_development else "disabled",
        "health": "/health",
        "metrics": "/metrics"
    }


# Export app for uvicorn
# Run with: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
