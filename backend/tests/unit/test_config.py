"""
Unit tests for app/config.py configuration management.

Tests verify:
- Environment variable loading
- Default values
- Type validation
- Custom validators
- Properties
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config import Settings


class TestSettings:
    """Test Settings configuration class."""

    def test_default_values(self):
        """Test that all settings have proper defaults."""
        settings = Settings()
        
        assert settings.database_url == "postgresql+asyncpg://tagmaster:tagmaster@db:5432/tagmaster"
        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_access_token_expire_minutes == 1440  # 24 hours
        assert settings.rate_limit_per_minute == 50
        assert settings.environment == "development"
        assert settings.log_level == "INFO"
        assert settings.monitoring_webhook_url == ""
        assert len(settings.cors_origins) == 2
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://localhost:8080" in settings.cors_origins

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
            "JWT_SECRET_KEY": "test-secret-key",
            "JWT_ALGORITHM": "HS512",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
            "RATE_LIMIT_PER_MINUTE": "100",
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "DEBUG",
            "MONITORING_WEBHOOK_URL": "https://example.com/webhook"
        }):
            settings = Settings()
            
            assert settings.database_url == "postgresql+asyncpg://test:test@localhost:5432/test"
            assert settings.jwt_secret_key == "test-secret-key"
            assert settings.jwt_algorithm == "HS512"
            assert settings.jwt_access_token_expire_minutes == 60
            assert settings.rate_limit_per_minute == 100
            assert settings.environment == "production"
            assert settings.log_level == "DEBUG"
            assert settings.monitoring_webhook_url == "https://example.com/webhook"

    def test_cors_origins_from_json(self):
        """Test CORS origins parsing from JSON array (pydantic-settings format)."""
        with patch.dict(os.environ, {
            "CORS_ORIGINS": '["http://example.com", "http://test.com", "http://localhost:5000"]'
        }):
            settings = Settings()
            
            assert len(settings.cors_origins) == 3
            assert "http://example.com" in settings.cors_origins
            assert "http://test.com" in settings.cors_origins
            assert "http://localhost:5000" in settings.cors_origins

    def test_is_production_property(self):
        """Test is_production property."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False

    def test_is_development_property(self):
        """Test is_development property."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            settings = Settings()
            assert settings.is_development is True
            assert settings.is_production is False

    def test_is_production_case_insensitive(self):
        """Test environment check is case-insensitive."""
        with patch.dict(os.environ, {"ENVIRONMENT": "PRODUCTION"}):
            settings = Settings()
            assert settings.is_production is True
            assert settings.is_development is False

    def test_is_development_case_insensitive(self):
        """Test environment check is case-insensitive."""
        with patch.dict(os.environ, {"ENVIRONMENT": "Development"}):
            settings = Settings()
            assert settings.is_development is True
            assert settings.is_production is False

    def test_staging_environment(self):
        """Test staging environment properties."""
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}):
            settings = Settings()
            assert settings.is_production is False
            assert settings.is_development is False
            assert settings.environment == "staging"

    def test_invalid_jwt_expire_minutes_type(self):
        """Test that invalid type for JWT expiration raises validation error."""
        with patch.dict(os.environ, {"JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "not-a-number"}):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            errors = exc_info.value.errors()
            assert len(errors) > 0
            assert any("jwt_access_token_expire_minutes" in str(error.get("loc")) for error in errors)

    def test_invalid_rate_limit_type(self):
        """Test that invalid type for rate limit raises validation error."""
        with patch.dict(os.environ, {"RATE_LIMIT_PER_MINUTE": "invalid"}):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            errors = exc_info.value.errors()
            assert len(errors) > 0
            assert any("rate_limit_per_minute" in str(error.get("loc")) for error in errors)

    def test_jwt_secret_key_field(self):
        """Test JWT secret key can be set."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "custom-secret-key"}):
            settings = Settings()
            assert settings.jwt_secret_key == "custom-secret-key"

    def test_empty_cors_origins_json(self):
        """Test handling of empty CORS origins as empty JSON array."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "[]"}):
            settings = Settings()
            assert len(settings.cors_origins) == 0

    def test_case_insensitive_env_vars(self):
        """Test that environment variable names are case-insensitive."""
        with patch.dict(os.environ, {
            "database_url": "postgresql+asyncpg://lowercase:test@localhost:5432/test",
            "JWT_SECRET_KEY": "uppercase-key"
        }):
            settings = Settings()
            # Pydantic should handle both cases
            assert "localhost" in settings.database_url
            assert settings.jwt_secret_key == "uppercase-key"

    def test_all_fields_have_descriptions(self):
        """Test that all fields have descriptions for documentation."""
        settings = Settings()
        schema = settings.model_json_schema()
        
        # Check that key fields have descriptions
        properties = schema.get("properties", {})
        assert "database_url" in properties
        assert "description" in properties["database_url"]
        assert "jwt_secret_key" in properties
        assert "description" in properties["jwt_secret_key"]
        assert "rate_limit_per_minute" in properties
        assert "description" in properties["rate_limit_per_minute"]

    def test_jwt_access_token_expire_default(self):
        """Test JWT token expiration default is 24 hours."""
        settings = Settings()
        assert settings.jwt_access_token_expire_minutes == 1440  # 24 * 60

    def test_default_jwt_algorithm_is_hs256(self):
        """Test default JWT algorithm is HS256."""
        settings = Settings()
        assert settings.jwt_algorithm == "HS256"
