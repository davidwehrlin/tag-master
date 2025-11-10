"""
Database configuration and session management.

Provides async SQLAlchemy engine, session factory, and dependency injection
for database sessions in FastAPI endpoints.
"""
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models.base import Base


# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://tagmaster:tagmaster@db:5432/tagmaster")

# Create async engine
# echo=True enables SQL query logging (useful for development)
# pool_pre_ping=True ensures connections are alive before using them
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query debugging
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

# Session factory for creating database sessions
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    
    Usage in endpoints:
        @router.get("/players")
        async def list_players(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Player))
            return result.scalars().all()
    
    The session is automatically closed after the request completes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    NOTE: In production, use Alembic migrations instead of this function.
    This is only useful for testing or initial development setup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    
    Should be called during application shutdown.
    """
    await engine.dispose()
