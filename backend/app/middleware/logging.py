"""
Structured logging middleware with PII sanitization.

Uses structlog for JSON logging with automatic PII redaction.
"""
import logging
import sys
from typing import Any, Dict

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


# PII fields to sanitize in logs
PII_FIELDS = {"email", "password", "password_hash", "name", "bio", "ip_address", "client_host"}


def sanitize_pii(logger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Structlog processor that redacts PII fields.
    
    Args:
        logger: Logger instance
        method_name: Logging method name
        event_dict: Event dictionary to process
        
    Returns:
        Sanitized event dictionary
    """
    for key in list(event_dict.keys()):
        if key.lower() in PII_FIELDS:
            event_dict[key] = "[REDACTED]"
        elif isinstance(event_dict[key], dict):
            event_dict[key] = _sanitize_dict(event_dict[key])
    return event_dict


def _sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize dictionary values."""
    sanitized = {}
    for key, value in data.items():
        if key.lower() in PII_FIELDS:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_dict(value)
        else:
            sanitized[key] = value
    return sanitized


# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        sanitize_pii,  # Custom PII sanitizer
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Set up Python logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=getattr(logging, settings.log_level.upper())
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests and responses.
    
    Logs include:
    - Request method, path, query params
    - Response status code, processing time
    - Request ID for correlation
    - Automatic PII redaction
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = structlog.get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next):
        """
        Log each request and response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response from endpoint
        """
        import time
        import uuid
        
        # Generate request ID for correlation
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log incoming request
        self.logger.info(
            "http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_host=request.client.host if request.client else None
        )
        
        # Process request and measure time
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            self.logger.info(
                "http_response",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2)
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            
            # Log error without PII
            self.logger.error(
                "http_error",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error_type=type(exc).__name__,
                process_time_ms=round(process_time * 1000, 2),
                exc_info=True
            )
            raise


# Create logger instance for app-wide use
def get_logger(name: str):
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Structlog logger instance with PII sanitization
        
    Example:
        logger = get_logger(__name__)
        logger.info("user_registered", user_id=user.id, email=user.email)
        # Output: {"event": "user_registered", "user_id": "...", "email": "[REDACTED]"}
    """
    return structlog.get_logger(name)
