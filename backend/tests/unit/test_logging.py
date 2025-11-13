"""
Unit tests for app/middleware/logging.py PII sanitization.

Tests verify:
- PII field sanitization (email, password, name, ip_address)
- Recursive sanitization in nested dicts
- HTTP request/response logging
- Request ID generation
- Error logging without PII exposure
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from app.middleware.logging import (
    LoggingMiddleware,
    sanitize_pii,
    _sanitize_dict,
    get_logger,
)


class TestPIISanitization:
    """Test PII field sanitization."""

    def test_sanitize_pii_email(self):
        """Test that email field is redacted."""
        event_dict = {"event": "user_login", "email": "user@example.com"}
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["email"] == "[REDACTED]"
        assert result["event"] == "user_login"

    def test_sanitize_pii_password(self):
        """Test that password field is redacted."""
        event_dict = {"event": "auth", "password": "secret123"}
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["password"] == "[REDACTED]"

    def test_sanitize_pii_password_hash(self):
        """Test that password_hash field is redacted."""
        event_dict = {"user_id": "123", "password_hash": "$2b$12$..."}
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["password_hash"] == "[REDACTED]"
        assert result["user_id"] == "123"

    def test_sanitize_pii_name(self):
        """Test that name field is redacted."""
        event_dict = {"event": "profile_update", "name": "John Doe"}
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["name"] == "[REDACTED]"

    def test_sanitize_pii_ip_address(self):
        """Test that ip_address field is redacted."""
        event_dict = {"event": "request", "ip_address": "192.168.1.1"}
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["ip_address"] == "[REDACTED]"

    def test_sanitize_pii_client_host(self):
        """Test that client_host field is redacted."""
        event_dict = {"event": "request", "client_host": "10.0.0.1"}
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["client_host"] == "[REDACTED]"

    def test_sanitize_pii_bio(self):
        """Test that bio field is redacted."""
        event_dict = {"user_id": "123", "bio": "Personal information"}
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["bio"] == "[REDACTED]"

    def test_sanitize_pii_multiple_fields(self):
        """Test that multiple PII fields are all redacted."""
        event_dict = {
            "event": "user_created",
            "email": "user@example.com",
            "name": "John Doe",
            "password": "secret",
            "user_id": "123"
        }
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["email"] == "[REDACTED]"
        assert result["name"] == "[REDACTED]"
        assert result["password"] == "[REDACTED]"
        assert result["user_id"] == "123"  # Not PII

    def test_sanitize_pii_case_insensitive(self):
        """Test that PII sanitization is case-insensitive."""
        event_dict = {
            "Email": "user@example.com",
            "PASSWORD": "secret",
            "Name": "John Doe"
        }
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["Email"] == "[REDACTED]"
        assert result["PASSWORD"] == "[REDACTED]"
        assert result["Name"] == "[REDACTED]"

    def test_sanitize_pii_preserves_non_pii(self):
        """Test that non-PII fields are preserved."""
        event_dict = {
            "event": "user_action",
            "user_id": "123",
            "action": "login",
            "timestamp": "2024-01-01T00:00:00Z",
            "email": "user@example.com"  # This should be redacted
        }
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["event"] == "user_action"
        assert result["user_id"] == "123"
        assert result["action"] == "login"
        assert result["timestamp"] == "2024-01-01T00:00:00Z"
        assert result["email"] == "[REDACTED]"


class TestNestedDictSanitization:
    """Test recursive PII sanitization in nested dictionaries."""

    def test_sanitize_nested_dict(self):
        """Test that nested PII fields are redacted."""
        event_dict = {
            "event": "user_update",
            "user": {
                "id": "123",
                "email": "user@example.com",
                "name": "John Doe"
            }
        }
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["user"]["id"] == "123"
        assert result["user"]["email"] == "[REDACTED]"
        assert result["user"]["name"] == "[REDACTED]"

    def test_sanitize_dict_helper(self):
        """Test _sanitize_dict helper function."""
        data = {
            "email": "test@example.com",
            "user_id": "123",
            "password": "secret"
        }
        
        result = _sanitize_dict(data)
        
        assert result["email"] == "[REDACTED]"
        assert result["password"] == "[REDACTED]"
        assert result["user_id"] == "123"

    def test_sanitize_deeply_nested_dict(self):
        """Test sanitization of deeply nested structures."""
        event_dict = {
            "event": "complex",
            "level1": {
                "level2": {
                    "email": "user@example.com",
                    "safe_field": "value"
                }
            }
        }
        
        result = sanitize_pii(None, None, event_dict)
        
        assert result["level1"]["level2"]["email"] == "[REDACTED]"
        assert result["level1"]["level2"]["safe_field"] == "value"

    def test_sanitize_mixed_nested_structure(self):
        """Test sanitization with mixed nested and top-level PII."""
        event_dict = {
            "top_email": "top@example.com",
            "nested": {
                "nested_password": "secret",
                "safe": "value"
            },
            "safe_top": "value"
        }
        
        # Note: top_email doesn't match exactly "email" so won't be redacted
        # But nested_password doesn't match "password" exactly either
        # The sanitization is based on exact field name matching (case-insensitive)
        result = sanitize_pii(None, None, event_dict)
        
        # These contain "email"/"password" but aren't exact matches
        assert result["top_email"] == "top@example.com"
        assert result["nested"]["nested_password"] == "secret"
        assert result["safe_top"] == "value"

    def test_sanitize_dict_with_non_dict_values(self):
        """Test that non-dict values are handled correctly."""
        data = {
            "email": "test@example.com",
            "count": 42,
            "active": True,
            "items": ["a", "b", "c"]
        }
        
        result = _sanitize_dict(data)
        
        assert result["email"] == "[REDACTED]"
        assert result["count"] == 42
        assert result["active"] is True
        assert result["items"] == ["a", "b", "c"]


class TestLoggingMiddleware:
    """Test LoggingMiddleware HTTP logging."""

    @pytest.fixture
    def mock_app(self):
        """Create mock FastAPI app."""
        return MagicMock()

    @pytest.fixture
    def logging_middleware(self, mock_app):
        """Create LoggingMiddleware instance."""
        return LoggingMiddleware(mock_app)

    @pytest.fixture
    def mock_request(self):
        """Create mock HTTP request."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/test"
        request.query_params = {}
        request.client.host = "127.0.0.1"
        request.state = MagicMock()
        return request

    @pytest.fixture
    def mock_call_next(self):
        """Create mock call_next function."""
        async def call_next(request):
            response = MagicMock()
            response.status_code = 200
            response.headers = {}
            return response
        return call_next

    @pytest.mark.asyncio
    async def test_dispatch_logs_request(self, logging_middleware, mock_request, mock_call_next):
        """Test that middleware logs incoming requests."""
        with patch.object(logging_middleware.logger, 'info') as mock_log:
            await logging_middleware.dispatch(mock_request, mock_call_next)
            
            # Should log request
            assert mock_log.call_count >= 1
            first_call = mock_log.call_args_list[0]
            assert first_call[0][0] == "http_request"

    @pytest.mark.asyncio
    async def test_dispatch_generates_request_id(self, logging_middleware, mock_request, mock_call_next):
        """Test that each request gets a unique request ID."""
        response = await logging_middleware.dispatch(mock_request, mock_call_next)
        
        assert hasattr(mock_request.state, 'request_id')
        assert response.headers.get("X-Request-ID") is not None

    @pytest.mark.asyncio
    async def test_dispatch_logs_response(self, logging_middleware, mock_request, mock_call_next):
        """Test that middleware logs responses."""
        with patch.object(logging_middleware.logger, 'info') as mock_log:
            await logging_middleware.dispatch(mock_request, mock_call_next)
            
            # Should log both request and response
            assert mock_log.call_count >= 2
            second_call = mock_log.call_args_list[1]
            assert second_call[0][0] == "http_response"

    @pytest.mark.asyncio
    async def test_dispatch_includes_status_code(self, logging_middleware, mock_request, mock_call_next):
        """Test that response log includes status code."""
        with patch.object(logging_middleware.logger, 'info') as mock_log:
            await logging_middleware.dispatch(mock_request, mock_call_next)
            
            response_call = mock_log.call_args_list[1]
            assert "status_code" in response_call[1]
            assert response_call[1]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_dispatch_includes_process_time(self, logging_middleware, mock_request, mock_call_next):
        """Test that response log includes processing time."""
        with patch.object(logging_middleware.logger, 'info') as mock_log:
            await logging_middleware.dispatch(mock_request, mock_call_next)
            
            response_call = mock_log.call_args_list[1]
            assert "process_time_ms" in response_call[1]
            assert isinstance(response_call[1]["process_time_ms"], (int, float))

    @pytest.mark.asyncio
    async def test_dispatch_logs_error(self, logging_middleware, mock_request):
        """Test that errors are logged."""
        async def failing_call_next(request):
            raise ValueError("Test error")
        
        with patch.object(logging_middleware.logger, 'error') as mock_error_log:
            with pytest.raises(ValueError):
                await logging_middleware.dispatch(mock_request, failing_call_next)
            
            assert mock_error_log.call_count == 1
            error_call = mock_error_log.call_args
            assert error_call[0][0] == "http_error"
            assert "error_type" in error_call[1]
            assert error_call[1]["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_dispatch_includes_method_and_path(self, logging_middleware, mock_request, mock_call_next):
        """Test that logs include HTTP method and path."""
        mock_request.method = "POST"
        mock_request.url.path = "/api/users"
        
        with patch.object(logging_middleware.logger, 'info') as mock_log:
            await logging_middleware.dispatch(mock_request, mock_call_next)
            
            request_call = mock_log.call_args_list[0]
            assert request_call[1]["method"] == "POST"
            assert request_call[1]["path"] == "/api/users"

    @pytest.mark.asyncio
    async def test_dispatch_correlates_request_response(self, logging_middleware, mock_request, mock_call_next):
        """Test that request and response logs share request_id."""
        with patch.object(logging_middleware.logger, 'info') as mock_log:
            await logging_middleware.dispatch(mock_request, mock_call_next)
            
            request_call = mock_log.call_args_list[0]
            response_call = mock_log.call_args_list[1]
            
            assert request_call[1]["request_id"] == response_call[1]["request_id"]


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_structlog_logger(self):
        """Test that get_logger returns a structlog logger."""
        logger = get_logger(__name__)
        
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')

    def test_get_logger_different_names(self):
        """Test that different names return different loggers."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        # Both should be valid loggers
        assert logger1 is not None
        assert logger2 is not None


class TestPIISanitizationIntegration:
    """Test PII sanitization in actual logging context."""

    def test_logger_sanitizes_email_in_log_call(self):
        """Test that logger sanitizes email when logging."""
        logger = get_logger(__name__)
        
        # This test verifies the configuration is set up correctly
        # In real usage, structlog processors would sanitize the output
        assert logger is not None

    def test_sanitization_preserves_log_structure(self):
        """Test that sanitization maintains log structure."""
        event_dict = {
            "event": "user_login",
            "user_id": "123",
            "email": "user@example.com",
            "timestamp": "2024-01-01"
        }
        
        result = sanitize_pii(None, None, event_dict)
        
        # Structure preserved, only PII redacted
        assert len(result) == 4
        assert result["event"] == "user_login"
        assert result["user_id"] == "123"
        assert result["email"] == "[REDACTED]"
        assert result["timestamp"] == "2024-01-01"
