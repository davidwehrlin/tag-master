"""
Global error handling middleware.

Catches all unhandled exceptions and returns consistent error responses.
"""
import traceback
from typing import Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that catches all unhandled exceptions and returns structured error responses.
    
    Ensures clients always receive JSON error responses even when unexpected errors occur.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Catch and handle all exceptions.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response from endpoint or error response
        """
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # Get request ID for correlation
            request_id = getattr(request.state, "request_id", "unknown")
            
            # Log error without PII
            logger.error(
                "unhandled_exception",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error_type=type(exc).__name__,
                error_message=str(exc),
                exc_info=True
            )
            
            # Return generic error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "An unexpected error occurred. Please try again later.",
                    "request_id": request_id,
                    "error_type": type(exc).__name__
                }
            )
