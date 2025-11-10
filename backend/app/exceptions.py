"""
Custom exception classes for the application.

Provides semantic exceptions that map to specific HTTP status codes.
"""
from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Raised when authentication fails (invalid credentials, expired token, etc.)."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Raised when user lacks permission to perform an action."""
    
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundError(HTTPException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str = "Resource", detail: str = None):
        message = detail or f"{resource} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class ValidationError(HTTPException):
    """Raised when request data fails validation."""
    
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class RateLimitError(HTTPException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, detail: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)}
        )


class ConflictError(HTTPException):
    """Raised when request conflicts with existing data (e.g., duplicate email)."""
    
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class BadRequestError(HTTPException):
    """Raised when request is malformed or contains invalid data."""
    
    def __init__(self, detail: str = "Bad request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
