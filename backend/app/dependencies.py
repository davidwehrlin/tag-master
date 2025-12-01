"""
FastAPI dependencies for authentication and authorization.

Provides dependency injection for:
- Current authenticated user extraction from JWT
- Database session management
"""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth import decode_access_token

# HTTP Bearer token security scheme for JWT authentication
# This displays a simple "Bearer token" input in Swagger instead of OAuth2 password form
security = HTTPBearer(description="JWT Bearer token")


async def get_current_user(
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    FastAPI dependency that extracts and validates the current user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session
        
    Returns:
        Player model instance for the authenticated user
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
        
    Usage:
        @router.get("/me")
        async def get_profile(current_user = Depends(get_current_user)):
            return current_user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract token from Bearer credentials
    token = credentials.credentials
    
    # Decode JWT token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extract user ID from token
    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    try:
        user_id = UUID(user_id_str)
    except (ValueError, AttributeError):
        raise credentials_exception
    
    # Import here to avoid circular dependency
    from app.models.player import Player
    
    # Fetch user from database
    result = await db.execute(
        select(Player).where(
            Player.id == user_id,
            Player.deleted_at.is_(None)  # Exclude soft-deleted users
        )
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    FastAPI dependency that ensures the current user is active (not soft-deleted).
    
    This is redundant with get_current_user (which already checks deleted_at),
    but provided for semantic clarity in endpoints that emphasize active status.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Player model instance
        
    Usage:
        @router.get("/profile")
        async def get_profile(user = Depends(get_current_active_user)):
            return user
    """
    return current_user
