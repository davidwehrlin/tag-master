"""
Health check and metrics endpoints.

Provides service health status and Prometheus-compatible metrics.
"""
import time
from typing import Dict

from fastapi import APIRouter, Depends
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.database import get_db

router = APIRouter(tags=["health"])

# Prometheus metrics
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Check application health status.
    
    Returns service status and database connectivity.
    
    Returns:
        Dictionary with status and database health
        
    Example response:
        {
            "status": "healthy",
            "database": "connected"
        }
    """
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "timestamp": time.time()
    }


@router.get("/metrics")
async def metrics() -> Response:
    """
    Expose Prometheus-compatible metrics.
    
    Returns metrics in Prometheus text format for scraping.
    
    Returns:
        Plain text response with metrics
        
    Example response:
        # HELP http_requests_total Total HTTP requests
        # TYPE http_requests_total counter
        http_requests_total{method="GET",endpoint="/api/v1/players",status="200"} 1234.0
    """
    metrics_output = generate_latest()
    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST
    )
