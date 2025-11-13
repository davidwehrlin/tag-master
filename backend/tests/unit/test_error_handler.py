"""
Unit tests for app/middleware/error_handler.py and app/exceptions.py.

Tests verify:
- Custom exceptions map to correct HTTP status codes
- Error responses have consistent format
- Error handler middleware catches unhandled exceptions
- Request ID included in error responses
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.middleware.error_handler import ErrorHandlerMiddleware


class TestCustomExceptions:
    """Test custom exception status codes and formats."""

    def test_authentication_error_status_code(self):
        """Test AuthenticationError returns 401."""
        exc = AuthenticationError()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authentication_error_has_www_authenticate_header(self):
        """Test AuthenticationError includes WWW-Authenticate header."""
        exc = AuthenticationError()
        assert exc.headers.get("WWW-Authenticate") == "Bearer"

    def test_authentication_error_custom_detail(self):
        """Test AuthenticationError accepts custom detail."""
        exc = AuthenticationError(detail="Invalid token")
        assert exc.detail == "Invalid token"

    def test_authorization_error_status_code(self):
        """Test AuthorizationError returns 403."""
        exc = AuthorizationError()
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_authorization_error_custom_detail(self):
        """Test AuthorizationError accepts custom detail."""
        exc = AuthorizationError(detail="Admin only")
        assert exc.detail == "Admin only"

    def test_not_found_error_status_code(self):
        """Test NotFoundError returns 404."""
        exc = NotFoundError()
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_not_found_error_resource_name(self):
        """Test NotFoundError formats message with resource name."""
        exc = NotFoundError(resource="Player")
        assert "Player not found" in exc.detail

    def test_not_found_error_custom_detail(self):
        """Test NotFoundError accepts custom detail."""
        exc = NotFoundError(detail="Custom message")
        assert exc.detail == "Custom message"

    def test_validation_error_status_code(self):
        """Test ValidationError returns 422."""
        exc = ValidationError()
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_validation_error_custom_detail(self):
        """Test ValidationError accepts custom detail."""
        exc = ValidationError(detail="Email format invalid")
        assert exc.detail == "Email format invalid"

    def test_rate_limit_error_status_code(self):
        """Test RateLimitError returns 429."""
        exc = RateLimitError()
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_rate_limit_error_has_retry_after_header(self):
        """Test RateLimitError includes Retry-After header."""
        exc = RateLimitError(retry_after=120)
        assert exc.headers.get("Retry-After") == "120"

    def test_rate_limit_error_default_retry_after(self):
        """Test RateLimitError has default retry_after of 60."""
        exc = RateLimitError()
        assert exc.headers.get("Retry-After") == "60"

    def test_conflict_error_status_code(self):
        """Test ConflictError returns 409."""
        exc = ConflictError()
        assert exc.status_code == status.HTTP_409_CONFLICT

    def test_conflict_error_custom_detail(self):
        """Test ConflictError accepts custom detail."""
        exc = ConflictError(detail="Email already exists")
        assert exc.detail == "Email already exists"

    def test_bad_request_error_status_code(self):
        """Test BadRequestError returns 400."""
        exc = BadRequestError()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_bad_request_error_custom_detail(self):
        """Test BadRequestError accepts custom detail."""
        exc = BadRequestError(detail="Missing required field")
        assert exc.detail == "Missing required field"


class TestExceptionDefaults:
    """Test exception default messages."""

    def test_authentication_error_default_message(self):
        """Test AuthenticationError default message."""
        exc = AuthenticationError()
        assert exc.detail == "Authentication failed"

    def test_authorization_error_default_message(self):
        """Test AuthorizationError default message."""
        exc = AuthorizationError()
        assert "permission" in exc.detail.lower()

    def test_not_found_error_default_message(self):
        """Test NotFoundError default message."""
        exc = NotFoundError()
        assert "not found" in exc.detail.lower()

    def test_validation_error_default_message(self):
        """Test ValidationError default message."""
        exc = ValidationError()
        assert "validation" in exc.detail.lower()

    def test_rate_limit_error_default_message(self):
        """Test RateLimitError default message."""
        exc = RateLimitError()
        assert "rate limit" in exc.detail.lower()

    def test_conflict_error_default_message(self):
        """Test ConflictError default message."""
        exc = ConflictError()
        assert "conflict" in exc.detail.lower()

    def test_bad_request_error_default_message(self):
        """Test BadRequestError default message."""
        exc = BadRequestError()
        assert "bad request" in exc.detail.lower()


class TestErrorHandlerMiddleware:
    """Test ErrorHandlerMiddleware catches and handles exceptions."""

    @pytest.mark.asyncio
    async def test_middleware_allows_successful_requests(self):
        """Test middleware passes through successful requests."""
        middleware = ErrorHandlerMiddleware(app=MagicMock())
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        
        mock_response = MagicMock()
        mock_call_next = AsyncMock(return_value=mock_response)
        
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_middleware_catches_unhandled_exceptions(self):
        """Test middleware catches and handles exceptions."""
        middleware = ErrorHandlerMiddleware(app=MagicMock())
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.request_id = "test-request-123"
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        
        mock_call_next = AsyncMock(side_effect=ValueError("Test error"))
        
        with patch("app.middleware.error_handler.logger") as mock_logger:
            result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_middleware_returns_json_error_response(self):
        """Test middleware returns JSON formatted error."""
        middleware = ErrorHandlerMiddleware(app=MagicMock())
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.request_id = "test-request-456"
        mock_request.method = "POST"
        mock_request.url.path = "/api/test"
        
        mock_call_next = AsyncMock(side_effect=RuntimeError("Unexpected error"))
        
        with patch("app.middleware.error_handler.logger"):
            result = await middleware.dispatch(mock_request, mock_call_next)
        
        assert isinstance(result, JSONResponse)
        # Access the body content
        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_middleware_includes_request_id(self):
        """Test middleware includes request_id in error response."""
        middleware = ErrorHandlerMiddleware(app=MagicMock())
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.request_id = "req-789"
        mock_request.method = "DELETE"
        mock_request.url.path = "/api/resource"
        
        mock_call_next = AsyncMock(side_effect=Exception("Error"))
        
        with patch("app.middleware.error_handler.logger"):
            result = await middleware.dispatch(mock_request, mock_call_next)
        
        # The JSONResponse body attribute contains the content dict
        assert "request_id" in result.body.decode()

    @pytest.mark.asyncio
    async def test_middleware_logs_exception(self):
        """Test middleware logs exception details."""
        middleware = ErrorHandlerMiddleware(app=MagicMock())
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.request_id = "log-test-123"
        mock_request.method = "PATCH"
        mock_request.url.path = "/api/users"
        
        test_exception = KeyError("missing key")
        mock_call_next = AsyncMock(side_effect=test_exception)
        
        with patch("app.middleware.error_handler.logger") as mock_logger:
            await middleware.dispatch(mock_request, mock_call_next)
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert call_args[0][0] == "unhandled_exception"
            assert call_args[1]["request_id"] == "log-test-123"
            assert call_args[1]["method"] == "PATCH"
            assert call_args[1]["error_type"] == "KeyError"

    @pytest.mark.asyncio
    async def test_middleware_handles_missing_request_id(self):
        """Test middleware handles requests without request_id."""
        middleware = ErrorHandlerMiddleware(app=MagicMock())
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        # No request_id set
        delattr(mock_request.state, "request_id")
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        
        mock_call_next = AsyncMock(side_effect=Exception("Error"))
        
        with patch("app.middleware.error_handler.logger") as mock_logger:
            result = await middleware.dispatch(mock_request, mock_call_next)
            
            # Should use "unknown" as default
            call_args = mock_logger.error.call_args
            assert call_args[1]["request_id"] == "unknown"

    @pytest.mark.asyncio
    async def test_middleware_includes_error_type(self):
        """Test middleware includes error type in response."""
        middleware = ErrorHandlerMiddleware(app=MagicMock())
        
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        mock_request.state.request_id = "type-test"
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        
        mock_call_next = AsyncMock(side_effect=ZeroDivisionError("Division by zero"))
        
        with patch("app.middleware.error_handler.logger"):
            result = await middleware.dispatch(mock_request, mock_call_next)
        
        body = result.body.decode()
        assert "ZeroDivisionError" in body
        assert "error_type" in body
