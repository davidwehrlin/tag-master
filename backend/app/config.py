"""
Application configuration using Pydantic settings.

Loads configuration from environment variables with validation and type conversion.
"""
import os
from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables.
    Example: DATABASE_URL=postgresql+asyncpg://...
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://tagmaster:tagmaster@db:5432/tagmaster",
        description="Async PostgreSQL connection string"
    )
    
    # JWT Authentication
    jwt_secret_key: str = Field(
        default="your-secret-key-here-change-in-production-use-openssl-rand-hex-32",
        description="Secret key for JWT token signing (must be kept secure)"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=1440,  # 24 hours
        description="JWT token expiration time in minutes"
    )
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins (comma-separated in env)"
    )
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=50,
        description="Maximum API requests per minute per user"
    )
    
    # Monitoring
    monitoring_webhook_url: str = Field(
        default="",
        description="Webhook URL for critical error notifications (optional)"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        description="Environment name (development, staging, production)"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
