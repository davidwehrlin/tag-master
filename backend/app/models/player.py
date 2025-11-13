"""
Player model and related entities.

Represents authenticated user accounts with disc golf league participation.
Includes role-based access control (Player, TagMaster, Assistant).
"""
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, Index, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, SoftDeleteMixin


class PlayerRole(str, PyEnum):
    """
    Player role enumeration for role-based access control.
    
    - PLAYER: Standard user with read access and ability to manage own data
    - TAG_MASTER: League creator with full permissions for their leagues
    - ASSISTANT: League-specific helper role (tracked via LeagueAssistant entity)
    """
    PLAYER = "Player"
    TAG_MASTER = "TagMaster"
    ASSISTANT = "Assistant"  # League-specific, tracked via LeagueAssistant


class Player(BaseModel, SoftDeleteMixin):
    """
    Player entity representing an authenticated user account.
    
    Players can create leagues (becoming TagMasters), register for seasons,
    participate in rounds, and have their rankings tracked via tags.
    
    Soft deletion is used to preserve historical data (scores, tag history)
    while preventing future authentication.
    """
    
    __tablename__ = "players"
    
    # Authentication & Identity
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Player's email address (login credential)"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    name = Column(
        String(255),
        nullable=False,
        comment="Player's display name"
    )
    
    bio = Column(
        String(1000),
        nullable=True,
        comment="Optional player biography"
    )
    
    # Role-Based Access Control
    roles = Column(
        ARRAY(String),
        nullable=False,
        default=["Player"],
        comment="Array of role names (Player, TagMaster)"
    )
    
    # Email Verification (optional in MVP)
    email_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Email verification status"
    )
    
    # Relationships
    # Note: These are defined with string references to avoid circular imports
    # Actual relationships will be resolved when all models are loaded
    created_leagues = relationship(
        "League",
        back_populates="organizer",
        foreign_keys="League.organizer_id",
        cascade="all, delete-orphan"
    )
    
    tags = relationship(
        "Tag",
        back_populates="player",
        cascade="all, delete-orphan"
    )
    
    tag_history = relationship(
        "TagHistory",
        back_populates="player",
        cascade="all, delete-orphan"
    )
    
    participations = relationship(
        "Participation",
        back_populates="player",
        foreign_keys="Participation.player_id",
        cascade="all, delete-orphan"
    )
    
    created_rounds = relationship(
        "Round",
        back_populates="creator",
        foreign_keys="Round.creator_id",
        cascade="all, delete-orphan"
    )
    
    created_cards = relationship(
        "Card",
        back_populates="creator",
        foreign_keys="Card.creator_id",
        cascade="all, delete-orphan"
    )
    
    bets = relationship(
        "Bet",
        back_populates="player",
        cascade="all, delete-orphan"
    )
    
    assistant_assignments = relationship(
        "LeagueAssistant",
        back_populates="player",
        foreign_keys="LeagueAssistant.player_id",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_player_email", "email"),
        Index("idx_player_deleted", "deleted_at"),
    )
    
    def has_role(self, role: PlayerRole) -> bool:
        """Check if player has a specific role."""
        return role.value in self.roles
    
    def add_role(self, role: PlayerRole) -> None:
        """Add a role to the player if not already present."""
        if role.value not in self.roles:
            self.roles.append(role.value)
    
    def remove_role(self, role: PlayerRole) -> None:
        """Remove a role from the player."""
        if role.value in self.roles:
            self.roles.remove(role.value)
    
    def __repr__(self) -> str:
        """String representation showing player name and email."""
        return f"<Player(id={self.id}, name='{self.name}', email='{self.email}')>"
