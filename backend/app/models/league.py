"""
Minimal League model to satisfy relationships referenced by `Player`.

This file provides a lightweight schema so unit tests that import the
Player model can initialize mappers without failing due to a missing
`League` symbol. The full production model lives in other specs and is
not required for unit tests that mock DB interactions.
"""
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, SoftDeleteMixin


class League(BaseModel, SoftDeleteMixin):
    __tablename__ = "leagues"

    # Organizer reference (UUID) - use string reference to avoid import cycles
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)

    # Relationship back to organizer (Player.created_leagues uses back_populates="organizer")
    organizer = relationship("Player", back_populates="created_leagues")

    # For tests we don't need any other fields; SoftDeleteMixin provides `deleted_at`.
