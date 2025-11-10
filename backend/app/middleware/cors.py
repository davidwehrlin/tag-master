"""
CORS (Cross-Origin Resource Sharing) middleware configuration.

Allows frontend applications to make requests to the API from different origins.
"""
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def configure_cors(app):
    """
    Configure CORS middleware on FastAPI application.
    
    Args:
        app: FastAPI application instance
        
    Example:
        from fastapi import FastAPI
        app = FastAPI()
        configure_cors(app)
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # List of allowed origins
        allow_credentials=True,  # Allow cookies and authorization headers
        allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"],  # Allow all headers
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )
