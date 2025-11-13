"""
Player profile API endpoints.

Provides:
- GET /players/me - Get current user profile
- PUT /players/me - Update current user profile
- DELETE /players/me - Soft delete current user account
- GET /players - List all players (paginated)
- GET /players/{id} - Get player by ID

Thin layer over PlayerService for HTTP-specific concerns.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.player import Player
from app.schemas.player import PlayerListResponse, PlayerResponse, PlayerUpdate
from app.services.player import player_service

router = APIRouter(prefix="/players", tags=["Players"])


@router.get(
    "/me",
    response_model=PlayerResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile information"
)
async def get_my_profile(
    current_user: Annotated[Player, Depends(get_current_user)]
) -> PlayerResponse:
    """
    Get current authenticated user's profile.
    
    **Authentication**: Required (JWT token)
    
    **Response**:
    - Returns player profile with id, email, name, bio, roles, timestamps
    - Excludes sensitive data (password_hash)
    """
    return PlayerResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=PlayerResponse,
    summary="Update current user profile",
    description="Update the authenticated user's profile information"
)
async def update_my_profile(
    update_data: PlayerUpdate,
    current_user: Annotated[Player, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> PlayerResponse:
    """
    Update current authenticated user's profile.
    
    **Authentication**: Required (JWT token)
    
    **Updatable Fields**:
    - name: Display name (2-255 characters)
    - bio: Biography (max 1000 characters)
    - password: New password (must meet complexity requirements)
    
    **Validation**:
    - Password must be minimum 8 characters with uppercase, lowercase, and number
    - Name cannot be empty or whitespace only
    
    **Response**:
    - Returns updated player profile
    
    **Errors**:
    - 422: Validation error (weak password, invalid name, etc.)
    """
    # Use service layer for business logic
    updated_player = await player_service.update_player(db, current_user, update_data)
    
    return PlayerResponse.model_validate(updated_player)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user account",
    description="Soft delete the authenticated user's account (preserves historical data)"
)
async def delete_my_account(
    current_user: Annotated[Player, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    """
    Soft delete current authenticated user's account.
    
    **Authentication**: Required (JWT token)
    
    **Soft Deletion**:
    - Sets deleted_at timestamp
    - Prevents future authentication
    - Preserves historical data (scores, tag history, etc.)
    
    **Response**:
    - 204 No Content on success
    
    **Note**:
    - Cannot delete if player is organizer of active leagues
    - Historical participations and scores remain intact
    """
    try:
        # Use service layer for business logic and validation
        await player_service.soft_delete_player(db, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "",
    response_model=PlayerListResponse,
    summary="List all players",
    description="Returns a paginated list of all active players"
)
async def list_players(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Players per page")] = 20
) -> PlayerListResponse:
    """
    List all active players with pagination.
    
    **Authentication**: Required (JWT token)
    
    **Query Parameters**:
    - page: Page number (default: 1)
    - size: Players per page (default: 20, max: 100)
    
    **Response**:
    - total: Total number of players
    - page: Current page number
    - size: Players per page
    - pages: Total number of pages
    - players: List of player profiles
    
    **Note**:
    - Only returns non-deleted players
    - Results are ordered by name
    """
    # Use service layer for business logic
    players, total = await player_service.list_players(db, page, size)
    
    # Calculate total pages
    pages = (total + size - 1) // size  # Ceiling division
    
    return PlayerListResponse(
        total=total,
        page=page,
        size=size,
        pages=pages,
        players=[PlayerResponse.model_validate(player) for player in players]
    )


@router.get(
    "/{player_id}",
    response_model=PlayerResponse,
    summary="Get player by ID",
    description="Returns public profile information for a specific player"
)
async def get_player_by_id(
    player_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Player, Depends(get_current_user)]  # Authentication required
) -> PlayerResponse:
    """
    Get player profile by ID.
    
    **Authentication**: Required (JWT token)
    
    **Path Parameters**:
    - player_id: UUID of the player to retrieve
    
    **Response**:
    - Returns player profile
    
    **Errors**:
    - 404: Player not found or deleted
    """
    # Use service layer for business logic
    player = await player_service.get_player_by_id(db, player_id)
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    return PlayerResponse.model_validate(player)
