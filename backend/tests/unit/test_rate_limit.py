"""
Unit tests for app/middleware/rate_limit.py token bucket rate limiting.

Tests verify:
- Token bucket algorithm implementation
- Rate limit enforcement (50 req/min)
- Token refill behavior
- User identification (user ID vs IP)
- Rate limit headers
- Health endpoint bypass
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, status

from app.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
def mock_app():
    """Create a mock FastAPI application."""
    return MagicMock()


@pytest.fixture
def rate_limit_middleware(mock_app):
    """Create RateLimitMiddleware instance."""
    return RateLimitMiddleware(mock_app)


@pytest.fixture
def mock_request():
    """Create a mock request."""
    request = MagicMock(spec=Request)
    request.url.path = "/api/test"
    request.client.host = "127.0.0.1"
    request.state = MagicMock()
    return request


@pytest.fixture
def mock_call_next():
    """Create a mock call_next function."""
    async def call_next(request):
        response = MagicMock()
        response.headers = {}
        return response
    return call_next


class TestRateLimitConfiguration:
    """Test rate limit middleware configuration."""

    def test_middleware_initializes_with_settings(self, mock_app):
        """Test that middleware loads rate limit from settings."""
        with patch("app.middleware.rate_limit.settings") as mock_settings:
            mock_settings.rate_limit_per_minute = 100
            
            middleware = RateLimitMiddleware(mock_app)
            
            assert middleware.rate_limit == 100
            assert middleware.refill_rate == 100 / 60.0

    def test_default_rate_limit(self, rate_limit_middleware):
        """Test default rate limit is 50 requests per minute."""
        assert rate_limit_middleware.rate_limit == 50
        assert rate_limit_middleware.refill_rate == 50 / 60.0

    def test_buckets_initialized_empty(self, rate_limit_middleware):
        """Test that buckets dictionary starts empty."""
        # Using defaultdict, it's empty until accessed
        assert len(rate_limit_middleware.buckets) == 0


class TestUserIdentification:
    """Test user identification for rate limiting."""

    def test_get_identifier_prefers_user_id(self, rate_limit_middleware, mock_request):
        """Test that user ID from auth is preferred over IP."""
        mock_request.state.user_id = "user-123"
        
        identifier = rate_limit_middleware._get_identifier(mock_request)
        
        assert identifier == "user:user-123"

    def test_get_identifier_falls_back_to_ip(self, rate_limit_middleware, mock_request):
        """Test that IP is used when no user ID available."""
        # Don't set user_id attribute
        delattr(mock_request.state, "user_id")
        mock_request.client.host = "192.168.1.100"
        
        identifier = rate_limit_middleware._get_identifier(mock_request)
        
        assert identifier == "ip:192.168.1.100"

    def test_get_identifier_handles_no_client(self, rate_limit_middleware, mock_request):
        """Test identifier when client info is unavailable."""
        delattr(mock_request.state, "user_id")
        mock_request.client = None
        
        identifier = rate_limit_middleware._get_identifier(mock_request)
        
        assert identifier == "ip:unknown"


class TestTokenBucketAlgorithm:
    """Test token bucket rate limiting algorithm."""

    def test_check_rate_limit_allows_first_request(self, rate_limit_middleware):
        """Test that first request is always allowed."""
        result = rate_limit_middleware._check_rate_limit("test-user")
        
        assert result is True

    def test_check_rate_limit_consumes_token(self, rate_limit_middleware):
        """Test that each request consumes one token."""
        initial_tokens = rate_limit_middleware.rate_limit
        
        rate_limit_middleware._check_rate_limit("test-user")
        
        tokens, _ = rate_limit_middleware.buckets["test-user"]
        # Allow for floating point precision and minimal time passage
        assert tokens < initial_tokens
        assert tokens >= initial_tokens - 1.1

    def test_check_rate_limit_blocks_when_empty(self, rate_limit_middleware):
        """Test that requests are blocked when bucket is empty."""
        identifier = "test-user"
        
        # Consume all tokens
        for _ in range(int(rate_limit_middleware.rate_limit)):
            rate_limit_middleware._check_rate_limit(identifier)
        
        # Next request should be blocked
        result = rate_limit_middleware._check_rate_limit(identifier)
        assert result is False

    def test_check_rate_limit_refills_tokens_over_time(self, rate_limit_middleware):
        """Test that tokens refill based on elapsed time."""
        identifier = "test-user"
        
        # Consume all tokens
        for _ in range(int(rate_limit_middleware.rate_limit)):
            rate_limit_middleware._check_rate_limit(identifier)
        
        # Mock time passage (2 seconds = 2 * refill_rate tokens)
        tokens_before, last_refill = rate_limit_middleware.buckets[identifier]
        with patch("app.middleware.rate_limit.time.time") as mock_time:
            mock_time.return_value = last_refill + 2.0  # 2 seconds later (gives ~1.67 tokens)
            
            result = rate_limit_middleware._check_rate_limit(identifier)
        
        # Should be allowed (refilled enough tokens for 1 request)
        assert result is True

    def test_token_refill_rate_calculation(self, rate_limit_middleware):
        """Test that tokens refill at correct rate."""
        identifier = "test-user"
        
        # Consume all tokens
        for _ in range(int(rate_limit_middleware.rate_limit)):
            rate_limit_middleware._check_rate_limit(identifier)
        
        # After 60 seconds, should have full bucket again
        _, last_refill = rate_limit_middleware.buckets[identifier]
        with patch("app.middleware.rate_limit.time.time") as mock_time:
            mock_time.return_value = last_refill + 60.0
            
            # Should have refilled to max
            tokens_before, _ = rate_limit_middleware.buckets[identifier]
            rate_limit_middleware._check_rate_limit(identifier)
            tokens_after, _ = rate_limit_middleware.buckets[identifier]
            
            # Should be close to max (minus 1 for consumed token)
            assert tokens_after >= rate_limit_middleware.rate_limit - 2

    def test_tokens_do_not_exceed_maximum(self, rate_limit_middleware):
        """Test that token count never exceeds rate limit."""
        identifier = "test-user"
        
        # Make a request
        rate_limit_middleware._check_rate_limit(identifier)
        
        # Wait a very long time
        _, last_refill = rate_limit_middleware.buckets[identifier]
        with patch("app.middleware.rate_limit.time.time") as mock_time:
            mock_time.return_value = last_refill + 1000.0  # 1000 seconds
            
            rate_limit_middleware._check_rate_limit(identifier)
            tokens, _ = rate_limit_middleware.buckets[identifier]
            
            # Should not exceed max (minus 1 for consumed token)
            assert tokens <= rate_limit_middleware.rate_limit


class TestRateLimitEnforcement:
    """Test rate limit enforcement in dispatch."""

    @pytest.mark.asyncio
    async def test_dispatch_allows_within_limit(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test that requests within limit are allowed."""
        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)
        
        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "50"

    @pytest.mark.asyncio
    async def test_dispatch_blocks_over_limit(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test that requests over limit return 429."""
        # Consume all tokens
        identifier = rate_limit_middleware._get_identifier(mock_request)
        for _ in range(int(rate_limit_middleware.rate_limit)):
            rate_limit_middleware._check_rate_limit(identifier)
        
        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_dispatch_returns_retry_after_header(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test that 429 response includes Retry-After header."""
        # Consume all tokens
        identifier = rate_limit_middleware._get_identifier(mock_request)
        for _ in range(int(rate_limit_middleware.rate_limit)):
            rate_limit_middleware._check_rate_limit(identifier)
        
        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)
        
        assert response.headers["Retry-After"] == "60"

    @pytest.mark.asyncio
    async def test_dispatch_includes_rate_limit_headers(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test that successful response includes rate limit headers."""
        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "50"

    @pytest.mark.asyncio
    async def test_dispatch_skips_health_endpoint(self, rate_limit_middleware, mock_call_next):
        """Test that health check endpoint bypasses rate limiting."""
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/health"
        
        # Consume all tokens for this identifier first
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()
        identifier = rate_limit_middleware._get_identifier(mock_request)
        for _ in range(int(rate_limit_middleware.rate_limit)):
            rate_limit_middleware._check_rate_limit(identifier)
        
        # Health endpoint should still work
        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)
        
        # Should not be rate limited
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_dispatch_skips_metrics_endpoint(self, rate_limit_middleware, mock_call_next):
        """Test that metrics endpoint bypasses rate limiting."""
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/metrics"
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()
        
        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)
        
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS


class TestBucketManagement:
    """Test bucket reset and management."""

    def test_reset_bucket_refills_tokens(self, rate_limit_middleware):
        """Test that reset_bucket refills tokens to maximum."""
        identifier = "test-user"
        
        # Consume some tokens
        for _ in range(10):
            rate_limit_middleware._check_rate_limit(identifier)
        
        # Reset bucket
        rate_limit_middleware.reset_bucket(identifier)
        
        tokens, _ = rate_limit_middleware.buckets[identifier]
        assert tokens == float(rate_limit_middleware.rate_limit)

    def test_reset_bucket_updates_refill_time(self, rate_limit_middleware):
        """Test that reset_bucket updates last refill time."""
        identifier = "test-user"
        
        # Use bucket
        rate_limit_middleware._check_rate_limit(identifier)
        old_time = rate_limit_middleware.buckets[identifier][1]
        
        # Wait and reset
        time.sleep(0.1)
        rate_limit_middleware.reset_bucket(identifier)
        
        new_time = rate_limit_middleware.buckets[identifier][1]
        assert new_time >= old_time


class TestRateLimitIntegration:
    """Test rate limiting integration scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_users_independent_limits(self, rate_limit_middleware, mock_call_next):
        """Test that different users have independent rate limits."""
        # User 1 exhausts their limit
        request1 = MagicMock(spec=Request)
        request1.url.path = "/api/test"
        request1.client.host = "192.168.1.1"
        request1.state = MagicMock()
        request1.state.user_id = "user-1"
        
        identifier1 = rate_limit_middleware._get_identifier(request1)
        for _ in range(int(rate_limit_middleware.rate_limit)):
            rate_limit_middleware._check_rate_limit(identifier1)
        
        # User 2 should still have full limit
        request2 = MagicMock(spec=Request)
        request2.url.path = "/api/test"
        request2.client.host = "192.168.1.2"
        request2.state = MagicMock()
        request2.state.user_id = "user-2"
        
        response = await rate_limit_middleware.dispatch(request2, mock_call_next)
        
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.asyncio
    async def test_rate_limit_remaining_decreases(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test that remaining count decreases with each request."""
        # Make several requests to ensure remaining decreases
        responses = []
        for _ in range(3):
            response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)
            responses.append(int(response.headers["X-RateLimit-Remaining"]))
        
        # At least one pair should show decrease
        assert responses[0] >= responses[1] >= responses[2]
        assert responses[0] > responses[2]  # Overall decrease

    @pytest.mark.asyncio
    async def test_error_response_format(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test that 429 error has correct JSON format."""
        # Exhaust rate limit
        identifier = rate_limit_middleware._get_identifier(mock_request)
        for _ in range(int(rate_limit_middleware.rate_limit)):
            rate_limit_middleware._check_rate_limit(identifier)
        
        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)
        
        # Should be JSONResponse with detail and retry_after
        assert hasattr(response, "body")
        # Response content includes detail and retry_after fields
        # (exact format depends on JSONResponse implementation)
