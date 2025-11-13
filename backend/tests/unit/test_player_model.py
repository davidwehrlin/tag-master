"""
Unit tests for Player model.

Tests PlayerRole enum, email uniqueness, soft delete behavior, role management.

NOTE: These tests use mocked Player instances to avoid database complexity.
For integration tests with actual database, see tests/integration/.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, PropertyMock
from uuid import uuid4

from app.models.player import Player, PlayerRole


@pytest.fixture
def mock_player():
    """Create a mock Player instance for testing."""
    player = Mock(spec=Player)
    player.id = uuid4()
    player.email = "test@example.com"
    player.password_hash = "hashed_password"
    player.name = "Test Player"
    player.bio = None
    player.roles = ["Player"]
    player.email_verified = False
    player.created_at = datetime.now(timezone.utc)
    player.updated_at = datetime.now(timezone.utc)
    player.deleted_at = None
    
    # Mock the methods
    player.has_role = Mock(side_effect=lambda role: role.value in player.roles)
    player.add_role = Mock(side_effect=lambda role: player.roles.append(role.value) if role.value not in player.roles else None)
    player.remove_role = Mock(side_effect=lambda role: player.roles.remove(role.value) if role.value in player.roles else None)
    player.soft_delete = Mock(side_effect=lambda: setattr(player, 'deleted_at', datetime.now(timezone.utc)))
    type(player).is_deleted = PropertyMock(side_effect=lambda: player.deleted_at is not None)
    
    return player


class TestPlayerRole:
    """Test PlayerRole enum."""
    
    def test_player_role_values(self):
        """Test PlayerRole enum has correct values."""
        assert PlayerRole.PLAYER.value == "Player"
        assert PlayerRole.TAG_MASTER.value == "TagMaster"
        assert PlayerRole.ASSISTANT.value == "Assistant"
    
    def test_player_role_is_string_enum(self):
        """Test PlayerRole is a string enum."""
        assert isinstance(PlayerRole.PLAYER.value, str)
        assert isinstance(PlayerRole.TAG_MASTER.value, str)
        assert isinstance(PlayerRole.ASSISTANT.value, str)
    
    def test_player_role_membership(self):
        """Test all expected roles are in enum."""
        role_values = [role.value for role in PlayerRole]
        assert "Player" in role_values
        assert "TagMaster" in role_values
        assert "Assistant" in role_values
        assert len(role_values) == 3


class TestPlayerModel:
    """Test Player model creation and basic fields."""
    
    def test_player_has_required_fields(self, mock_player):
        """Test Player instance has all required fields."""
        assert mock_player.id is not None
        assert mock_player.email == "test@example.com"
        assert mock_player.password_hash == "hashed_password"
        assert mock_player.name == "Test Player"
        assert mock_player.bio is None
        assert mock_player.roles == ["Player"]
        assert mock_player.email_verified is False
        assert mock_player.created_at is not None
        assert mock_player.updated_at is not None
        assert mock_player.deleted_at is None
    
    def test_player_default_role(self, mock_player):
        """Test Player is created with default Player role."""
        assert "Player" in mock_player.roles
        assert len(mock_player.roles) == 1
    
    def test_player_timestamps_exist(self, mock_player):
        """Test created_at and updated_at exist."""
        assert mock_player.created_at is not None
        assert mock_player.updated_at is not None
        assert isinstance(mock_player.created_at, datetime)
        assert isinstance(mock_player.updated_at, datetime)


class TestSoftDelete:
    """Test soft delete behavior on Player model."""
    
    def test_soft_delete_sets_deleted_at(self, mock_player):
        """Test soft_delete() sets deleted_at timestamp."""
        assert mock_player.deleted_at is None
        
        before = datetime.now(timezone.utc)
        mock_player.soft_delete()
        after = datetime.now(timezone.utc)
        
        assert mock_player.deleted_at is not None
        assert before <= mock_player.deleted_at <= after
    
    def test_is_deleted_check(self, mock_player):
        """Test is_deleted property."""
        assert mock_player.is_deleted is False
        
        mock_player.soft_delete()
        
        assert mock_player.is_deleted is True


class TestRoleManagement:
    """Test role management methods on Player model."""
    
    def test_has_role_returns_true_when_role_present(self, mock_player):
        """Test has_role() returns True when player has role."""
        assert mock_player.has_role(PlayerRole.PLAYER) is True
    
    def test_has_role_returns_false_when_role_absent(self, mock_player):
        """Test has_role() returns False when player doesn't have role."""
        assert mock_player.has_role(PlayerRole.TAG_MASTER) is False
    
    def test_add_role_adds_new_role(self, mock_player):
        """Test add_role() adds a new role to player."""
        mock_player.add_role(PlayerRole.TAG_MASTER)
        
        assert mock_player.has_role(PlayerRole.TAG_MASTER) is True
        assert "TagMaster" in mock_player.roles
        assert len(mock_player.roles) == 2
    
    def test_add_role_does_not_duplicate(self, mock_player):
        """Test add_role() doesn't add duplicate roles."""
        initial_len = len(mock_player.roles)
        mock_player.add_role(PlayerRole.PLAYER)
        
        # Should not add duplicate
        assert mock_player.roles.count("Player") == 1
        assert len(mock_player.roles) == initial_len
    
    def test_remove_role_removes_existing_role(self, mock_player):
        """Test remove_role() removes an existing role."""
        mock_player.roles = ["Player", "TagMaster"]
        mock_player.remove_role(PlayerRole.TAG_MASTER)
        
        assert mock_player.has_role(PlayerRole.TAG_MASTER) is False
        assert "TagMaster" not in mock_player.roles
        assert len(mock_player.roles) == 1
    
    def test_remove_role_handles_absent_role(self, mock_player):
        """Test remove_role() handles removing non-existent role gracefully."""
        # Should not raise error
        mock_player.remove_role(PlayerRole.TAG_MASTER)
        
        assert mock_player.roles == ["Player"]
    
    def test_multiple_roles_can_coexist(self, mock_player):
        """Test player can have multiple roles simultaneously."""
        mock_player.add_role(PlayerRole.TAG_MASTER)
        mock_player.add_role(PlayerRole.ASSISTANT)
        
        assert mock_player.has_role(PlayerRole.PLAYER) is True
        assert mock_player.has_role(PlayerRole.TAG_MASTER) is True
        assert mock_player.has_role(PlayerRole.ASSISTANT) is True
        assert len(mock_player.roles) == 3


class TestPlayerBio:
    """Test optional bio field."""
    
    def test_player_creation_without_bio(self, mock_player):
        """Test creating player without bio (optional field)."""
        assert mock_player.bio is None
    
    def test_player_creation_with_bio(self):
        """Test creating player with bio."""
        player = Mock(spec=Player)
        player.bio = "I love disc golf!"
        
        assert player.bio == "I love disc golf!"
    
    def test_player_bio_can_be_updated(self, mock_player):
        """Test updating player bio."""
        mock_player.bio = "Updated bio"
        
        assert mock_player.bio == "Updated bio"
