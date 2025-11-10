"""
Role-Based Access Control (RBAC) utilities for permission checking.

Provides functions to check if a user has permission to perform actions
on leagues, rounds, and other resources.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def is_tag_master(player) -> bool:
    """
    Check if a player has the TagMaster role.
    
    Args:
        player: Player model instance
        
    Returns:
        True if player has TagMaster role, False otherwise
    """
    return "TagMaster" in player.roles


async def can_manage_league(player, league_id: UUID, db: AsyncSession) -> bool:
    """
    Check if a player can manage a specific league.
    
    A player can manage a league if they are:
    - The league organizer, OR
    - An assigned assistant for the league
    
    Args:
        player: Player model instance
        league_id: UUID of the league to check
        db: Database session
        
    Returns:
        True if player can manage the league, False otherwise
    """
    # Import here to avoid circular dependency
    from app.models.league import League
    from app.models.league_assistant import LeagueAssistant
    
    # Check if player is the organizer
    result = await db.execute(
        select(League).where(
            League.id == league_id,
            League.organizer_id == player.id,
            League.deleted_at.is_(None)
        )
    )
    league = result.scalar_one_or_none()
    if league:
        return True
    
    # Check if player is an assigned assistant
    result = await db.execute(
        select(LeagueAssistant).where(
            LeagueAssistant.league_id == league_id,
            LeagueAssistant.player_id == player.id
        )
    )
    assistant = result.scalar_one_or_none()
    
    return assistant is not None


async def can_manage_round(player, round_id: UUID, db: AsyncSession) -> bool:
    """
    Check if a player can manage a specific round.
    
    A player can manage a round if they can manage its parent league.
    
    Args:
        player: Player model instance
        round_id: UUID of the round to check
        db: Database session
        
    Returns:
        True if player can manage the round, False otherwise
    """
    # Import here to avoid circular dependency
    from app.models.round import Round
    from app.models.season import Season
    
    # Get round and its season
    result = await db.execute(
        select(Round).where(
            Round.id == round_id,
            Round.deleted_at.is_(None)
        )
    )
    round_obj = result.scalar_one_or_none()
    if not round_obj:
        return False
    
    # Get season and its league
    result = await db.execute(
        select(Season).where(Season.id == round_obj.season_id)
    )
    season = result.scalar_one_or_none()
    if not season:
        return False
    
    # Check league permissions
    return await can_manage_league(player, season.league_id, db)


async def is_tag_master_or_assistant(player, league_id: UUID, db: AsyncSession) -> bool:
    """
    Check if a player is a TagMaster or an assistant for a specific league.
    
    This is a convenience function combining both checks.
    
    Args:
        player: Player model instance
        league_id: UUID of the league to check
        db: Database session
        
    Returns:
        True if player is TagMaster or assistant for the league, False otherwise
    """
    if await is_tag_master(player):
        return await can_manage_league(player, league_id, db)
    return False


async def require_league_manager(player, league_id: UUID, db: AsyncSession) -> None:
    """
    Raise an exception if player cannot manage the league.
    
    Args:
        player: Player model instance
        league_id: UUID of the league to check
        db: Database session
        
    Raises:
        HTTPException: 403 if player cannot manage the league
    """
    from fastapi import HTTPException, status
    
    if not await can_manage_league(player, league_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage this league"
        )


async def require_round_manager(player, round_id: UUID, db: AsyncSession) -> None:
    """
    Raise an exception if player cannot manage the round.
    
    Args:
        player: Player model instance
        round_id: UUID of the round to check
        db: Database session
        
    Raises:
        HTTPException: 403 if player cannot manage the round
    """
    from fastapi import HTTPException, status
    
    if not await can_manage_round(player, round_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage this round"
        )
