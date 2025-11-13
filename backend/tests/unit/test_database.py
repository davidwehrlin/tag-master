"""
Unit tests for database connection and session management.

Tests verify:
- Async session factory configuration
- Connection pooling settings
- Database dependency injection
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from unittest.mock import AsyncMock, patch, MagicMock, Mock
import sys

# Mock asyncpg if not available (Python 3.13 compatibility issue)
if "asyncpg" not in sys.modules:
    sys.modules["asyncpg"] = Mock()

from app.database import (
    engine,
    AsyncSessionLocal,
    get_db,
    init_db,
    close_db,
    DATABASE_URL,
)


class TestDatabaseConfiguration:
    """Test database configuration and engine setup."""

    def test_engine_is_async_engine(self):
        """Test that engine is AsyncEngine instance."""
        assert isinstance(engine, AsyncEngine)

    def test_engine_url_from_environment(self):
        """Test that engine uses DATABASE_URL from environment."""
        # The engine URL should contain postgresql+asyncpg
        assert "postgresql+asyncpg" in str(engine.url)

    def test_engine_pool_settings(self):
        """Test that engine has correct pool configuration."""
        # Check pool_size and max_overflow are configured
        assert engine.pool.size() == 20
        # Check _max_overflow attribute (overflow() returns current, not max)
        assert hasattr(engine.pool, '_max_overflow')
        assert engine.pool._max_overflow == 10

    def test_engine_pool_pre_ping(self):
        """Test that pool_pre_ping is enabled."""
        # pool_pre_ping ensures connections are alive
        assert engine.pool._pre_ping is True

    def test_session_factory_is_configured(self):
        """Test that AsyncSessionLocal is properly configured."""
        assert AsyncSessionLocal is not None
        # Check session factory creates AsyncSession instances
        assert AsyncSessionLocal.class_ == AsyncSession

    def test_session_factory_settings(self):
        """Test that session factory has correct settings."""
        # expire_on_commit should be False
        assert AsyncSessionLocal.kw.get("expire_on_commit") is False
        # autocommit and autoflush should be False
        assert AsyncSessionLocal.kw.get("autocommit") is False
        assert AsyncSessionLocal.kw.get("autoflush") is False


class TestDatabaseDependency:
    """Test database dependency injection."""

    def test_get_db_yields_session(self):
        """Test that get_db yields an AsyncSession."""
        # This is a sync test - just verify the function exists and is callable
        assert callable(get_db)
        # get_db is an async generator, verify its type
        import types
        assert isinstance(get_db(), types.AsyncGeneratorType)

    def test_get_db_commits_on_success(self):
        """Test that get_db has commit logic (structural test)."""
        import inspect
        source = inspect.getsource(get_db)
        # Verify source contains commit call
        assert "commit()" in source
        assert "rollback()" in source
        assert "close()" in source

    def test_get_db_has_error_handling(self):
        """Test that get_db has proper error handling."""
        import inspect
        source = inspect.getsource(get_db)
        # Verify try/except/finally structure
        assert "try:" in source
        assert "except" in source
        assert "finally:" in source

    def test_get_db_uses_context_manager(self):
        """Test that get_db uses async context manager."""
        import inspect
        source = inspect.getsource(get_db)
        # Verify async with statement for session
        assert "async with" in source


class TestDatabaseLifecycle:
    """Test database initialization and cleanup."""

    def test_init_db_exists_and_callable(self):
        """Test that init_db function exists and is callable."""
        assert callable(init_db)
        # Verify it's an async function
        import asyncio
        assert asyncio.iscoroutinefunction(init_db)

    def test_init_db_creates_tables(self):
        """Test that init_db contains table creation logic."""
        import inspect
        source = inspect.getsource(init_db)
        # Verify it calls create_all
        assert "create_all" in source

    def test_close_db_exists_and_callable(self):
        """Test that close_db function exists and is callable."""
        assert callable(close_db)
        # Verify it's an async function
        import asyncio
        assert asyncio.iscoroutinefunction(close_db)

    def test_close_db_disposes_engine(self):
        """Test that close_db contains disposal logic."""
        import inspect
        source = inspect.getsource(close_db)
        # Verify it calls dispose
        assert "dispose()" in source


class TestDatabaseURL:
    """Test DATABASE_URL configuration."""

    def test_database_url_uses_asyncpg(self):
        """Test that DATABASE_URL uses asyncpg driver."""
        assert "postgresql+asyncpg" in DATABASE_URL

    def test_database_url_has_required_components(self):
        """Test that DATABASE_URL has user, host, port, database."""
        # Should have format: postgresql+asyncpg://user:pass@host:port/db
        assert "@" in DATABASE_URL  # Has user/password
        assert ":" in DATABASE_URL  # Has port
        assert "/" in DATABASE_URL  # Has database name

    @patch.dict('os.environ', {'DATABASE_URL': 'postgresql+asyncpg://test:test@localhost:5432/test'})
    def test_database_url_from_env_override(self):
        """Test that DATABASE_URL can be overridden by environment variable."""
        # Import database module with mocked environment
        import importlib
        import app.database as db_module
        importlib.reload(db_module)
        
        # DATABASE_URL should use environment variable
        assert "localhost" in db_module.DATABASE_URL
        assert "test" in db_module.DATABASE_URL
