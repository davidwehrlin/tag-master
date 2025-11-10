"""
Base models for SQLAlchemy ORM.

Provides abstract base classes with common fields (UUID primary key, timestamps)
and soft deletion support for all models in the application.
"""
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    
    pass


class BaseModel(Base):
    """
    Abstract base model with UUID primary key and timestamp fields.
    
    All models should inherit from this to ensure consistent:
    - UUID-based primary keys (not auto-incrementing integers)
    - Automatic created_at timestamp on insert
    - Automatic updated_at timestamp on update
    """
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        comment="Unique identifier"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when record was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Timestamp when record was last updated"
    )
    
    def __repr__(self) -> str:
        """String representation showing class name and ID."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class SoftDeleteMixin:
    """
    Mixin for entities that support soft deletion.
    
    Soft deletion preserves historical data by marking records as deleted
    rather than physically removing them from the database. This is critical
    for maintaining audit trails (e.g., tag history, round scores).
    
    Usage:
        class Player(BaseModel, SoftDeleteMixin):
            __tablename__ = "players"
            # ... other fields
    
    The deleted_at field is indexed for efficient filtering of active records.
    """
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp when record was soft-deleted (null if active)"
    )
    
    @property
    def is_deleted(self) -> bool:
        """Check if this record has been soft-deleted."""
        return self.deleted_at is not None
    
    def soft_delete(self) -> None:
        """Mark this record as deleted."""
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
