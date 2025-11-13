"""
Player service layer.

Handles all business logic for player operations including:
- Registration and authentication
- Profile management (CRUD)
- Validation and authorization
"""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import Player, PlayerRole
from app.schemas.player import PlayerRegister, PlayerUpdate
from app.services.auth import hash_password, verify_password


class PlayerService:
    """
    Service class for player-related business logic.
    
    Separates business logic from API endpoint handlers for:
    - Better testability (can unit test without FastAPI)
    - Reusability (can call from CLI, background jobs, etc.)
    - Maintainability (business logic changes don't affect routing)
    """
    
    async def register_player(
        self, 
        db: AsyncSession, 
        player_data: PlayerRegister
    ) -> Player:
        """
        Register a new player account.
        
        Args:
            db: Database session
            player_data: Validated registration data
            
        Returns:
            Created Player instance
            
        Raises:
            ValueError: If email already registered
        """
        # Check if email already exists (non-deleted players only)
        result = await db.execute(
            select(Player).where(
                Player.email == player_data.email,
                Player.deleted_at.is_(None)
            )
        )
        existing_player = result.scalar_one_or_none()
        
        if existing_player:
            raise ValueError("Email already registered")
        
        # Hash password
        password_hash = hash_password(player_data.password)
        
        # Create new player with default Player role
        new_player = Player(
            email=player_data.email,
            password_hash=password_hash,
            name=player_data.name,
            bio=player_data.bio,
            roles=[PlayerRole.PLAYER.value],
            email_verified=False
        )
        
        db.add(new_player)
        await db.commit()
        await db.refresh(new_player)
        
        return new_player
    
    async def authenticate_player(
        self, 
        db: AsyncSession, 
        email: str, 
        password: str
    ) -> Optional[Player]:
        """
        Authenticate player with email and password.
        
        Args:
            db: Database session
            email: Player email address
            password: Plain-text password
            
        Returns:
            Player instance if authentication successful, None otherwise
        """
        # Find player by email (non-deleted only)
        result = await db.execute(
            select(Player).where(
                Player.email == email,
                Player.deleted_at.is_(None)
            )
        )
        player = result.scalar_one_or_none()
        
        # Verify password
        if not player or not verify_password(password, player.password_hash):
            return None
        
        return player
    
    async def get_player_by_id(
        self, 
        db: AsyncSession, 
        player_id: UUID
    ) -> Optional[Player]:
        """
        Get player by ID (non-deleted only).
        
        Args:
            db: Database session
            player_id: Player UUID
            
        Returns:
            Player instance if found, None otherwise
        """
        result = await db.execute(
            select(Player).where(
                Player.id == player_id,
                Player.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()
    
    async def update_player(
        self, 
        db: AsyncSession, 
        player: Player, 
        update_data: PlayerUpdate
    ) -> Player:
        """
        Update player profile.
        
        Args:
            db: Database session
            player: Player instance to update
            update_data: Validated update data
            
        Returns:
            Updated Player instance
        """
        # Update name if provided
        if update_data.name is not None:
            player.name = update_data.name
        
        # Update bio if provided
        if update_data.bio is not None:
            player.bio = update_data.bio
        
        # Update password if provided
        if update_data.password is not None:
            player.password_hash = hash_password(update_data.password)
        
        await db.commit()
        await db.refresh(player)
        
        return player
    
    async def soft_delete_player(
        self, 
        db: AsyncSession, 
        player: Player
    ) -> None:
        """
        Soft delete player account.
        
        Validates that player can be deleted (no active leagues as organizer).
        
        Args:
            db: Database session
            player: Player instance to delete
            
        Raises:
            ValueError: If player is organizer of active leagues
        """
        # Check if player is organizer of any active leagues
        from app.models import League
        
        result = await db.execute(
            select(func.count()).select_from(League).where(
                League.organizer_id == player.id,
                League.deleted_at.is_(None)
            )
        )
        active_leagues_count = result.scalar_one()
        
        if active_leagues_count > 0:
            raise ValueError(
                f"Cannot delete account: organizer of {active_leagues_count} active league(s). "
                "Please delete or transfer leagues first."
            )
        
        # Soft delete the player
        player.soft_delete()
        await db.commit()
    
    async def list_players(
        self, 
        db: AsyncSession, 
        page: int = 1, 
        size: int = 20
    ) -> Tuple[List[Player], int]:
        """
        List all active players with pagination.
        
        Args:
            db: Database session
            page: Page number (1-indexed)
            size: Players per page
            
        Returns:
            Tuple of (list of players, total count)
        """
        # Count total non-deleted players
        count_query = select(func.count()).select_from(Player).where(
            Player.deleted_at.is_(None)
        )
        result = await db.execute(count_query)
        total = result.scalar_one()
        
        # Get paginated players ordered by name
        query = (
            select(Player)
            .where(Player.deleted_at.is_(None))
            .order_by(Player.name)
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db.execute(query)
        players = list(result.scalars().all())
        
        return players, total
    
    async def assign_tagmaster_role(
        self, 
        db: AsyncSession, 
        player: Player
    ) -> Player:
        """
        Assign TagMaster role to player (called when creating first league).
        
        Args:
            db: Database session
            player: Player instance
            
        Returns:
            Updated Player instance
        """
        if not player.has_role(PlayerRole.TAG_MASTER):
            player.add_role(PlayerRole.TAG_MASTER)
            await db.commit()
            await db.refresh(player)
        
        return player


# Global service instance
player_service = PlayerService()
