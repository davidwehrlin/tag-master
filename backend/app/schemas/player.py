"""
Pydantic schemas for Player entity.

Defines request/response models for player authentication and profile management.
"""
import re
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class PlayerRegister(BaseModel):
    """
    Request schema for player registration.
    
    Validates email format, password complexity, and name requirements.
    """
    email: EmailStr = Field(
        ...,
        description="Player's email address (must be unique)",
        examples=["player@example.com"]
    )
    
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 chars, must contain uppercase, lowercase, and number)",
        examples=["SecurePass123"]
    )
    
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Player's display name",
        examples=["John Doe"]
    )
    
    bio: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional player biography",
        examples=["Disc golf enthusiast since 2020"]
    )
    
    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """
        Validate password complexity requirements.
        
        Must contain:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        """
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()


class PlayerLogin(BaseModel):
    """Request schema for player login."""
    email: EmailStr = Field(
        ...,
        description="Player's email address",
        examples=["player@example.com"]
    )
    
    password: str = Field(
        ...,
        description="Player's password",
        examples=["SecurePass123"]
    )


class TokenResponse(BaseModel):
    """
    Response schema for successful authentication.
    
    Returns JWT access token with player information.
    """
    access_token: str = Field(
        ...,
        description="JWT access token for authentication",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
        examples=["bearer"]
    )
    
    player_id: UUID = Field(
        ...,
        description="Unique player identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    email: EmailStr = Field(
        ...,
        description="Player's email address",
        examples=["player@example.com"]
    )
    
    name: str = Field(
        ...,
        description="Player's display name",
        examples=["John Doe"]
    )
    
    roles: List[str] = Field(
        ...,
        description="Player's roles (e.g., ['Player', 'TagMaster'])",
        examples=[["Player"]]
    )


class PlayerResponse(BaseModel):
    """
    Response schema for player profile information.
    
    Excludes sensitive data like password_hash.
    """
    id: UUID = Field(
        ...,
        description="Unique player identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    
    email: EmailStr = Field(
        ...,
        description="Player's email address",
        examples=["player@example.com"]
    )
    
    name: str = Field(
        ...,
        description="Player's display name",
        examples=["John Doe"]
    )
    
    bio: Optional[str] = Field(
        None,
        description="Player's biography",
        examples=["Disc golf enthusiast since 2020"]
    )
    
    roles: List[str] = Field(
        ...,
        description="Player's roles",
        examples=[["Player", "TagMaster"]]
    )
    
    email_verified: bool = Field(
        ...,
        description="Email verification status",
        examples=[False]
    )
    
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
        examples=["2025-01-01T12:00:00Z"]
    )
    
    updated_at: datetime = Field(
        ...,
        description="Last profile update timestamp",
        examples=["2025-01-15T14:30:00Z"]
    )
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True  # Enable ORM mode for SQLAlchemy models


class PlayerUpdate(BaseModel):
    """
    Request schema for updating player profile.
    
    All fields are optional - only provided fields will be updated.
    """
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Updated display name",
        examples=["Jane Smith"]
    )
    
    bio: Optional[str] = Field(
        None,
        max_length=1000,
        description="Updated biography",
        examples=["Professional disc golfer"]
    )
    
    password: Optional[str] = Field(
        None,
        min_length=8,
        description="New password (must meet complexity requirements)",
        examples=["NewSecurePass456"]
    )
    
    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: Optional[str]) -> Optional[str]:
        """Validate password complexity if provided."""
        if v is None:
            return v
        
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name if provided."""
        if v is None:
            return v
        
        if not v or not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        return v.strip()


class PlayerListResponse(BaseModel):
    """
    Response schema for paginated player list.
    
    Used by GET /players endpoint.
    """
    total: int = Field(
        ...,
        description="Total number of players matching filter",
        examples=[42]
    )
    
    page: int = Field(
        ...,
        description="Current page number (1-indexed)",
        examples=[1]
    )
    
    size: int = Field(
        ...,
        description="Number of players per page",
        examples=[20]
    )
    
    pages: int = Field(
        ...,
        description="Total number of pages",
        examples=[3]
    )
    
    players: List[PlayerResponse] = Field(
        ...,
        description="List of players on current page"
    )


class ErrorResponse(BaseModel):
    """Generic error response schema."""
    detail: str = Field(
        ...,
        description="Error message",
        examples=["Email already registered"]
    )
