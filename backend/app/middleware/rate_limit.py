"""
Rate limiting middleware using token bucket algorithm.

Implements in-memory rate limiting with 50 requests per minute per user.
"""
import time
from collections import defaultdict
from typing import Callable, Dict, Tuple

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware.
    
    Tracks request counts per user (identified by IP or user ID) and enforces
    rate limits based on configuration.
    
    Algorithm: Token Bucket
    - Each user has a bucket with N tokens
    - Each request consumes 1 token
    - Tokens refill at a constant rate
    - If bucket is empty, request is rejected
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Store: {identifier: (token_count, last_refill_time)}
        self.buckets: Dict[str, Tuple[float, float]] = defaultdict(
            lambda: (float(settings.rate_limit_per_minute), time.time())
        )
        self.rate_limit = settings.rate_limit_per_minute
        self.refill_rate = self.rate_limit / 60.0  # tokens per second
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and enforce rate limiting.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response from endpoint or 429 rate limit error
        """
        # Skip rate limiting for health check endpoints
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # Identify user (prefer user ID from JWT, fallback to IP)
        identifier = self._get_identifier(request)
        
        # Check and update rate limit
        if not self._check_rate_limit(identifier):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {self.rate_limit} requests per minute.",
                    "retry_after": 60  # seconds
                },
                headers={"Retry-After": "60"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        remaining = int(self.buckets[identifier][0])
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting.
        
        Prefers user ID from JWT token, falls back to IP address.
        
        Args:
            request: Incoming HTTP request
            
        Returns:
            Unique identifier string
        """
        # Try to extract user ID from request state (set by auth middleware)
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Fallback to client IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    def _check_rate_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limit using token bucket algorithm.
        
        Args:
            identifier: Unique user/IP identifier
            
        Returns:
            True if request allowed, False if rate limit exceeded
        """
        current_time = time.time()
        tokens, last_refill = self.buckets[identifier]
        
        # Refill tokens based on elapsed time
        time_elapsed = current_time - last_refill
        tokens_to_add = time_elapsed * self.refill_rate
        tokens = min(self.rate_limit, tokens + tokens_to_add)
        
        # Check if enough tokens available
        if tokens < 1.0:
            # Update bucket state (no token consumed)
            self.buckets[identifier] = (tokens, current_time)
            return False
        
        # Consume one token
        tokens -= 1.0
        self.buckets[identifier] = (tokens, current_time)
        return True
    
    def reset_bucket(self, identifier: str) -> None:
        """
        Reset rate limit bucket for a specific identifier.
        
        Useful for testing or admin overrides.
        
        Args:
            identifier: Unique user/IP identifier to reset
        """
        self.buckets[identifier] = (float(self.rate_limit), time.time())
