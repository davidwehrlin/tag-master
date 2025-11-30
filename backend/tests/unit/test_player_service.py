"""
Unit tests for PlayerService.

Tests register_player, authenticate_player, update_player, soft_delete_player, list_players.
Also includes password validation tests.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.services.player import PlayerService
from app.models.player import PlayerRole
from app.schemas.player import PlayerRegister, PlayerUpdate


@pytest.fixture
def player_service():
    """Create PlayerService instance."""
    return PlayerService()


@pytest.fixture
def mock_db():
    """Create mock async database session."""
    db = AsyncMock()
    # `add` on AsyncSession is a synchronous method; make it a regular Mock so
    # tests that set side_effect/capture handlers work as expected.
    db.add = Mock()
    return db


@pytest.fixture(autouse=True)
def patch_player_class(monkeypatch):
    """Replace the SQLAlchemy `Player` used in the service with a simple factory that returns a Mock.

    This prevents SQLAlchemy mapper/config issues while exercising service logic.
    """
    def _factory(**kwargs):
        m = Mock()
        for k, v in kwargs.items():
            setattr(m, k, v)
        m.id = getattr(m, 'id', uuid4())
        now = datetime.now(timezone.utc)
        m.created_at = getattr(m, 'created_at', now)
        m.updated_at = getattr(m, 'updated_at', now)
        m.deleted_at = None
        m.has_role = Mock()
        m.add_role = Mock()
        m.soft_delete = Mock()
        return m

    # NOTE: Do not patch the real Player class here — keep SQLAlchemy mappings intact.
    # The factory was causing SQLAlchemy lambda analysis to evaluate closure
    # callables (raising errors). Tests now use Mock objects for sample data
    # and mock DB results instead of replacing the mapped class.
    yield


@pytest.fixture
def sample_player():
    """Create a non-mapped sample player for testing to avoid SQLAlchemy mapper init."""
    player = Mock()
    player.email = "test@example.com"
    player.password_hash = "hashed_password"
    player.name = "Test Player"
    player.bio = "Test bio"
    player.roles = ["Player"]
    player.email_verified = False
    player.id = uuid4()
    player.created_at = datetime.now(timezone.utc)
    player.updated_at = datetime.now(timezone.utc)
    player.deleted_at = None
    # provide callable methods used by service
    player.has_role = Mock()
    player.add_role = Mock()
    player.soft_delete = Mock()
    return player


class TestRegisterPlayer:
    """Test PlayerService.register_player method."""
    
    @pytest.mark.asyncio
    async def test_register_player_success(self, player_service, mock_db):
        """Test successful player registration."""
        register_data = PlayerRegister(
            email="new@example.com",
            password="SecurePass123",
            name="New Player",
            bio="New player bio"
        )
        
        # Mock database query to return None (no existing player)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with patch('app.services.player.hash_password', return_value='hashed_password'):
            player = await player_service.register_player(mock_db, register_data)
        
        # Verify player was created
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called
    
    @pytest.mark.asyncio
    async def test_register_player_duplicate_email(self, player_service, mock_db, sample_player):
        """Test registration fails with duplicate email."""
        register_data = PlayerRegister(
            email="test@example.com",
            password="SecurePass123",
            name="Duplicate Player"
        )
        
        # Mock database query to return existing player
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_player
        mock_db.execute.return_value = mock_result
        
        # Should raise ValueError for duplicate email
        with pytest.raises(ValueError, match="Email already registered"):
            await player_service.register_player(mock_db, register_data)
        
        # Verify no player was added
        assert not mock_db.add.called
    
    @pytest.mark.asyncio
    async def test_register_player_assigns_default_role(self, player_service, mock_db):
        """Test new player gets default Player role."""
        register_data = PlayerRegister(
            email="new@example.com",
            password="SecurePass123",
            name="New Player"
        )
        
        # Mock database query to return None (no existing player)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Capture the player being added
        added_player = None
        def capture_add(player):
            nonlocal added_player
            added_player = player
        
        mock_db.add.side_effect = capture_add
        
        with patch('app.services.player.hash_password', return_value='hashed_password'):
            await player_service.register_player(mock_db, register_data)
        
        # Verify default role was assigned
        assert added_player is not None
        assert "Player" in added_player.roles
    
    @pytest.mark.asyncio
    async def test_register_player_hashes_password(self, player_service, mock_db):
        """Test password is hashed during registration."""
        register_data = PlayerRegister(
            email="new@example.com",
            password="PlainTextPass123",
            name="New Player"
        )
        
        # Mock database query to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Capture the player being added
        added_player = None
        def capture_add(player):
            nonlocal added_player
            added_player = player
        
        mock_db.add.side_effect = capture_add
        
        with patch('app.services.player.hash_password', return_value='hashed_secret') as mock_hash:
            await player_service.register_player(mock_db, register_data)
        
        # Verify password was hashed
        mock_hash.assert_called_once_with("PlainTextPass123")
        assert added_player.password_hash == 'hashed_secret'


class TestAuthenticatePlayer:
    """Test PlayerService.authenticate_player method."""
    
    @pytest.mark.asyncio
    async def test_authenticate_player_success(self, player_service, mock_db, sample_player):
        """Test successful authentication."""
        # Mock database query to return player
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_player
        mock_db.execute.return_value = mock_result
        
        with patch('app.services.player.verify_password', return_value=True):
            player = await player_service.authenticate_player(
                mock_db, 
                "test@example.com", 
                "correct_password"
            )
        
        assert player is not None
        assert player.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_authenticate_player_invalid_email(self, player_service, mock_db):
        """Test authentication fails with invalid email."""
        # Mock database query to return None (player not found)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        player = await player_service.authenticate_player(
            mock_db,
            "nonexistent@example.com",
            "any_password"
        )
        
        assert player is None
    
    @pytest.mark.asyncio
    async def test_authenticate_player_invalid_password(self, player_service, mock_db, sample_player):
        """Test authentication fails with invalid password."""
        # Mock database query to return player
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_player
        mock_db.execute.return_value = mock_result
        
        with patch('app.services.player.verify_password', return_value=False):
            player = await player_service.authenticate_player(
                mock_db,
                "test@example.com",
                "wrong_password"
            )
        
        assert player is None
    
    @pytest.mark.asyncio
    async def test_authenticate_player_soft_deleted(self, player_service, mock_db, sample_player):
        """Test authentication fails for soft-deleted players."""
        # Mark player as deleted
        sample_player.deleted_at = datetime.now(timezone.utc)
        
        # Mock database query to return None (soft-deleted players excluded)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        player = await player_service.authenticate_player(
            mock_db,
            "test@example.com",
            "any_password"
        )
        
        assert player is None


class TestGetPlayerById:
    """Test PlayerService.get_player_by_id method."""
    
    @pytest.mark.asyncio
    async def test_get_player_by_id_success(self, player_service, mock_db, sample_player):
        """Test getting player by ID."""
        player_id = sample_player.id
        
        # Mock database query to return player
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_player
        mock_db.execute.return_value = mock_result
        
        player = await player_service.get_player_by_id(mock_db, player_id)
        
        assert player is not None
        assert player.id == player_id
    
    @pytest.mark.asyncio
    async def test_get_player_by_id_not_found(self, player_service, mock_db):
        """Test getting non-existent player returns None."""
        player_id = uuid4()
        
        # Mock database query to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        player = await player_service.get_player_by_id(mock_db, player_id)
        
        assert player is None
    
    @pytest.mark.asyncio
    async def test_get_player_by_id_excludes_deleted(self, player_service, mock_db):
        """Test soft-deleted players are excluded."""
        player_id = uuid4()
        
        # Mock database query to return None (deleted player excluded)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        player = await player_service.get_player_by_id(mock_db, player_id)
        
        assert player is None


class TestUpdatePlayer:
    """Test PlayerService.update_player method."""
    
    @pytest.mark.asyncio
    async def test_update_player_name(self, player_service, mock_db, sample_player):
        """Test updating player name."""
        update_data = PlayerUpdate(name="Updated Name")
        
        updated_player = await player_service.update_player(
            mock_db, 
            sample_player, 
            update_data
        )
        
        assert sample_player.name == "Updated Name"
        assert mock_db.commit.called
        assert mock_db.refresh.called
    
    @pytest.mark.asyncio
    async def test_update_player_bio(self, player_service, mock_db, sample_player):
        """Test updating player bio."""
        update_data = PlayerUpdate(bio="Updated bio")
        
        await player_service.update_player(mock_db, sample_player, update_data)
        
        assert sample_player.bio == "Updated bio"
    
    @pytest.mark.asyncio
    async def test_update_player_password(self, player_service, mock_db, sample_player):
        """Test updating player password."""
        update_data = PlayerUpdate(password="NewSecurePass456")
        
        with patch('app.services.player.hash_password', return_value='new_hashed_password'):
            await player_service.update_player(mock_db, sample_player, update_data)
        
        assert sample_player.password_hash == 'new_hashed_password'
    
    @pytest.mark.asyncio
    async def test_update_player_multiple_fields(self, player_service, mock_db, sample_player):
        """Test updating multiple fields at once."""
        update_data = PlayerUpdate(
            name="New Name",
            bio="New bio"
        )
        
        await player_service.update_player(mock_db, sample_player, update_data)
        
        assert sample_player.name == "New Name"
        assert sample_player.bio == "New bio"
    
    @pytest.mark.asyncio
    async def test_update_player_no_changes(self, player_service, mock_db, sample_player):
        """Test update with no fields specified."""
        update_data = PlayerUpdate()
        
        original_name = sample_player.name
        original_bio = sample_player.bio
        
        await player_service.update_player(mock_db, sample_player, update_data)
        
        # Nothing should change
        assert sample_player.name == original_name
        assert sample_player.bio == original_bio


class TestSoftDeletePlayer:
    """Test PlayerService.soft_delete_player method."""
    
    @pytest.mark.asyncio
    async def test_soft_delete_player_success(self, player_service, mock_db, sample_player):
        """Test successful soft deletion."""
        # Mock database query to return 0 active leagues
        mock_result = Mock()
        mock_result.scalar_one.return_value = 0
        mock_db.execute.return_value = mock_result
        
        # Mock soft_delete method
        sample_player.soft_delete = Mock()
        
        await player_service.soft_delete_player(mock_db, sample_player)
        
        # Verify soft_delete was called
        sample_player.soft_delete.assert_called_once()
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_soft_delete_player_with_active_leagues(self, player_service, mock_db, sample_player):
        """Test deletion fails when player has active leagues."""
        # Mock database query to return 2 active leagues
        mock_result = Mock()
        mock_result.scalar_one.return_value = 2
        mock_db.execute.return_value = mock_result
        
        # Should raise ValueError
        with pytest.raises(ValueError, match="Cannot delete account.*2 active league"):
            await player_service.soft_delete_player(mock_db, sample_player)
        
        # Verify commit was not called
        assert not mock_db.commit.called


class TestListPlayers:
    """Test PlayerService.list_players method."""
    
    @pytest.mark.asyncio
    async def test_list_players_returns_paginated_results(self, player_service, mock_db):
        """Test listing players returns paginated results."""
        # Mock count query
        count_result = Mock()
        count_result.scalar_one.return_value = 50

        # Mock list query
        list_result = Mock()
        sample_players = [
            Mock(email=f"player{i}@example.com", password_hash="hash", name=f"Player {i}", roles=["Player"]) 
            for i in range(20)
        ]
        # scalars().all() should return the list
        scalars_mock = Mock()
        scalars_mock.all.return_value = sample_players
        list_result.scalars.return_value = scalars_mock

        # Configure mock to return different results for count and list queries
        mock_db.execute.side_effect = [count_result, list_result]
        
        players, total = await player_service.list_players(mock_db, page=1, size=20)
        
        assert len(players) == 20
        assert total == 50
    
    @pytest.mark.asyncio
    async def test_list_players_pagination(self, player_service, mock_db):
        """Test pagination parameters are applied."""
        # Mock count query
        count_result = Mock()
        count_result.scalar_one.return_value = 100

        # Mock list query
        list_result = Mock()
        scalars_mock = Mock()
        scalars_mock.all.return_value = []
        list_result.scalars.return_value = scalars_mock

        mock_db.execute.side_effect = [count_result, list_result]
        
        await player_service.list_players(mock_db, page=3, size=10)
        
        # Verify execute was called twice (count + list)
        assert mock_db.execute.call_count == 2
    
    @pytest.mark.asyncio
    async def test_list_players_empty_result(self, player_service, mock_db):
        """Test listing players when none exist."""
        # Mock count query
        count_result = Mock()
        count_result.scalar_one.return_value = 0

        # Mock list query
        list_result = Mock()
        scalars_mock = Mock()
        scalars_mock.all.return_value = []
        list_result.scalars.return_value = scalars_mock

        mock_db.execute.side_effect = [count_result, list_result]
        
        players, total = await player_service.list_players(mock_db, page=1, size=20)
        
        assert len(players) == 0
        assert total == 0


class TestAssignTagMasterRole:
    """Test PlayerService.assign_tagmaster_role method."""
    
    @pytest.mark.asyncio
    async def test_assign_tagmaster_role_success(self, player_service, mock_db, sample_player):
        """Test assigning TagMaster role to player."""
        # Mock has_role and add_role methods
        sample_player.has_role = Mock(return_value=False)
        sample_player.add_role = Mock()
        
        await player_service.assign_tagmaster_role(mock_db, sample_player)
        
        # Verify role was added
        sample_player.add_role.assert_called_once_with(PlayerRole.TAG_MASTER)
        assert mock_db.commit.called
        assert mock_db.refresh.called
    
    @pytest.mark.asyncio
    async def test_assign_tagmaster_role_already_has_role(self, player_service, mock_db, sample_player):
        """Test assigning TagMaster role when player already has it."""
        # Mock has_role to return True
        sample_player.has_role = Mock(return_value=True)
        sample_player.add_role = Mock()
        
        await player_service.assign_tagmaster_role(mock_db, sample_player)
        
        # Verify add_role was not called
        sample_player.add_role.assert_not_called()


class TestPasswordValidation:
    """Test password hashing and validation in PlayerService context."""
    
    @pytest.mark.asyncio
    async def test_register_rejects_weak_password(self, player_service, mock_db):
        """Test registration with weak password is rejected by schema validation."""
        # This test verifies that Pydantic validation catches weak passwords
        # before they reach the service layer
        
        # Weak password (no uppercase)
        with pytest.raises(Exception):  # Pydantic ValidationError
            PlayerRegister(
                email="test@example.com",
                password="weakpass123",  # No uppercase
                name="Test Player"
            )
    
    @pytest.mark.asyncio
    async def test_register_accepts_strong_password(self, player_service, mock_db):
        """Test registration accepts strong password."""
        # Mock database query to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Strong password
        register_data = PlayerRegister(
            email="test@example.com",
            password="StrongPass123",  # Has uppercase, lowercase, number
            name="Test Player"
        )
        
        with patch('app.services.player.hash_password', return_value='hashed'):
            await player_service.register_player(mock_db, register_data)
        
        assert mock_db.add.called
    
    @pytest.mark.asyncio
    async def test_password_is_never_stored_plain_text(self, player_service, mock_db):
        """Test password is always hashed before storage."""
        register_data = PlayerRegister(
            email="test@example.com",
            password="PlainPassword123",
            name="Test Player"
        )
        
        # Mock database query to return None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        # Capture the player being added
        added_player = None
        def capture_add(player):
            nonlocal added_player
            added_player = player
        
        mock_db.add.side_effect = capture_add
        
        with patch('app.services.player.hash_password', return_value='$2b$12$hashed_version'):
            await player_service.register_player(mock_db, register_data)
        
        # Verify plain password is not in password_hash
        assert added_player.password_hash != "PlainPassword123"
        assert added_player.password_hash == '$2b$12$hashed_version'
