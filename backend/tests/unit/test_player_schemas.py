"""
Unit tests for Player Pydantic schemas.

Tests email validation, password validation, schema serialization.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.player import (
    PlayerRegister,
    PlayerLogin,
    TokenResponse,
    PlayerResponse,
    PlayerUpdate,
    PlayerListResponse,
    ErrorResponse
)


class TestPlayerRegisterSchema:
    """Test PlayerRegister schema validation."""
    
    def test_valid_registration_data(self):
        """Test valid registration data passes validation."""
        data = PlayerRegister(
            email="test@example.com",
            password="SecurePass123",
            name="Test Player",
            bio="Test bio"
        )
        
        assert data.email == "test@example.com"
        assert data.password == "SecurePass123"
        assert data.name == "Test Player"
        assert data.bio == "Test bio"
    
    def test_registration_without_bio(self):
        """Test registration without optional bio field."""
        data = PlayerRegister(
            email="test@example.com",
            password="SecurePass123",
            name="Test Player"
        )
        
        assert data.bio is None
    
    def test_invalid_email_format(self):
        """Test invalid email format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerRegister(
                email="invalid-email",
                password="SecurePass123",
                name="Test Player"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('email',) for error in errors)
    
    def test_password_too_short(self):
        """Test password less than 8 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerRegister(
                email="test@example.com",
                password="Short1",  # Only 6 characters
                name="Test Player"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('password',) for error in errors)
    
    def test_password_no_uppercase(self):
        """Test password without uppercase letter is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerRegister(
                email="test@example.com",
                password="lowercase123",
                name="Test Player"
            )
        
        errors = exc_info.value.errors()
        assert any('uppercase' in str(error).lower() for error in errors)
    
    def test_password_no_lowercase(self):
        """Test password without lowercase letter is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerRegister(
                email="test@example.com",
                password="UPPERCASE123",
                name="Test Player"
            )
        
        errors = exc_info.value.errors()
        assert any('lowercase' in str(error).lower() for error in errors)
    
    def test_password_no_number(self):
        """Test password without number is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerRegister(
                email="test@example.com",
                password="NoNumbersHere",
                name="Test Player"
            )
        
        errors = exc_info.value.errors()
        assert any('number' in str(error).lower() for error in errors)
    
    def test_password_meets_all_requirements(self):
        """Test password meeting all complexity requirements."""
        # Should not raise
        data = PlayerRegister(
            email="test@example.com",
            password="ValidPass123",  # Has uppercase, lowercase, number, 8+ chars
            name="Test Player"
        )
        
        assert data.password == "ValidPass123"
    
    def test_name_too_short(self):
        """Test name less than 2 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerRegister(
                email="test@example.com",
                password="SecurePass123",
                name="A"  # Only 1 character
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('name',) for error in errors)
    
    def test_name_too_long(self):
        """Test name exceeding 255 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerRegister(
                email="test@example.com",
                password="SecurePass123",
                name="A" * 256  # 256 characters
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('name',) for error in errors)
    
    def test_name_empty_string(self):
        """Test empty name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerRegister(
                email="test@example.com",
                password="SecurePass123",
                name=""
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('name',) for error in errors)
    
    def test_name_whitespace_only(self):
        """Test name with only whitespace is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerRegister(
                email="test@example.com",
                password="SecurePass123",
                name="   "
            )
        
        errors = exc_info.value.errors()
        assert any('empty' in str(error).lower() for error in errors)
    
    def test_name_whitespace_trimmed(self):
        """Test name whitespace is trimmed."""
        data = PlayerRegister(
            email="test@example.com",
            password="SecurePass123",
            name="  Test Player  "
        )
        
        assert data.name == "Test Player"
    
    def test_bio_max_length(self):
        """Test bio exceeding 1000 characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerRegister(
                email="test@example.com",
                password="SecurePass123",
                name="Test Player",
                bio="A" * 1001  # 1001 characters
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('bio',) for error in errors)
    
    def test_bio_exactly_1000_characters(self):
        """Test bio with exactly 1000 characters is accepted."""
        # Should not raise
        data = PlayerRegister(
            email="test@example.com",
            password="SecurePass123",
            name="Test Player",
            bio="A" * 1000  # Exactly 1000 characters
        )
        
        assert len(data.bio) == 1000


class TestPlayerLoginSchema:
    """Test PlayerLogin schema validation."""
    
    def test_valid_login_data(self):
        """Test valid login data passes validation."""
        data = PlayerLogin(
            email="test@example.com",
            password="SecurePass123"
        )
        
        assert data.email == "test@example.com"
        assert data.password == "SecurePass123"
    
    def test_invalid_email_format(self):
        """Test invalid email format is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerLogin(
                email="not-an-email",
                password="SecurePass123"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('email',) for error in errors)


class TestTokenResponseSchema:
    """Test TokenResponse schema."""
    
    def test_token_response_creation(self):
        """Test creating TokenResponse."""
        player_id = uuid4()
        
        response = TokenResponse(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            token_type="bearer",
            player_id=player_id,
            email="test@example.com",
            name="Test Player",
            roles=["Player"]
        )
        
        assert response.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert response.token_type == "bearer"
        assert response.player_id == player_id
        assert response.email == "test@example.com"
        assert response.name == "Test Player"
        assert response.roles == ["Player"]
    
    def test_token_response_default_token_type(self):
        """Test TokenResponse has default token_type."""
        player_id = uuid4()
        
        response = TokenResponse(
            access_token="token",
            player_id=player_id,
            email="test@example.com",
            name="Test Player",
            roles=["Player"]
        )
        
        assert response.token_type == "bearer"


class TestPlayerResponseSchema:
    """Test PlayerResponse schema."""
    
    def test_player_response_serialization(self):
        """Test PlayerResponse can serialize player data."""
        player_id = uuid4()
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        response = PlayerResponse(
            id=player_id,
            email="test@example.com",
            name="Test Player",
            bio="Test bio",
            roles=["Player", "TagMaster"],
            email_verified=True,
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert response.id == player_id
        assert response.email == "test@example.com"
        assert response.name == "Test Player"
        assert response.bio == "Test bio"
        assert response.roles == ["Player", "TagMaster"]
        assert response.email_verified is True
        assert response.created_at == created_at
        assert response.updated_at == updated_at
    
    def test_player_response_without_bio(self):
        """Test PlayerResponse with None bio."""
        player_id = uuid4()
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        response = PlayerResponse(
            id=player_id,
            email="test@example.com",
            name="Test Player",
            bio=None,
            roles=["Player"],
            email_verified=False,
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert response.bio is None


class TestPlayerUpdateSchema:
    """Test PlayerUpdate schema validation."""
    
    def test_update_name_only(self):
        """Test updating only name field."""
        data = PlayerUpdate(name="New Name")
        
        assert data.name == "New Name"
        assert data.bio is None
        assert data.password is None
    
    def test_update_bio_only(self):
        """Test updating only bio field."""
        data = PlayerUpdate(bio="New bio")
        
        assert data.bio == "New bio"
        assert data.name is None
        assert data.password is None
    
    def test_update_password_only(self):
        """Test updating only password field."""
        data = PlayerUpdate(password="NewSecurePass456")
        
        assert data.password == "NewSecurePass456"
        assert data.name is None
        assert data.bio is None
    
    def test_update_multiple_fields(self):
        """Test updating multiple fields."""
        data = PlayerUpdate(
            name="New Name",
            bio="New bio",
            password="NewSecurePass456"
        )
        
        assert data.name == "New Name"
        assert data.bio == "New bio"
        assert data.password == "NewSecurePass456"
    
    def test_update_no_fields(self):
        """Test update with no fields specified."""
        data = PlayerUpdate()
        
        assert data.name is None
        assert data.bio is None
        assert data.password is None
    
    def test_update_password_complexity_validation(self):
        """Test password complexity is validated on update."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerUpdate(password="weak")
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('password',) for error in errors)
    
    def test_update_name_validation(self):
        """Test name validation on update."""
        with pytest.raises(ValidationError) as exc_info:
            PlayerUpdate(name="   ")  # Whitespace only
        
        errors = exc_info.value.errors()
        assert any('empty' in str(error).lower() for error in errors)
    
    def test_update_name_whitespace_trimmed(self):
        """Test name whitespace is trimmed on update."""
        data = PlayerUpdate(name="  Updated Name  ")
        
        assert data.name == "Updated Name"


class TestPlayerListResponseSchema:
    """Test PlayerListResponse schema."""
    
    def test_player_list_response_creation(self):
        """Test creating PlayerListResponse."""
        player_id = uuid4()
        created_at = datetime.now(timezone.utc)
        updated_at = datetime.now(timezone.utc)
        
        player = PlayerResponse(
            id=player_id,
            email="test@example.com",
            name="Test Player",
            bio=None,
            roles=["Player"],
            email_verified=False,
            created_at=created_at,
            updated_at=updated_at
        )
        
        response = PlayerListResponse(
            total=100,
            page=1,
            size=20,
            pages=5,
            players=[player]
        )
        
        assert response.total == 100
        assert response.page == 1
        assert response.size == 20
        assert response.pages == 5
        assert len(response.players) == 1
        assert response.players[0].email == "test@example.com"
    
    def test_player_list_response_empty(self):
        """Test PlayerListResponse with empty player list."""
        response = PlayerListResponse(
            total=0,
            page=1,
            size=20,
            pages=0,
            players=[]
        )
        
        assert response.total == 0
        assert len(response.players) == 0


class TestErrorResponseSchema:
    """Test ErrorResponse schema."""
    
    def test_error_response_creation(self):
        """Test creating ErrorResponse."""
        response = ErrorResponse(detail="Something went wrong")
        
        assert response.detail == "Something went wrong"


class TestSchemaIntegration:
    """Test schema integration and serialization."""
    
    def test_registration_to_response_flow(self):
        """Test typical flow from registration to response."""
        # Registration
        register = PlayerRegister(
            email="newuser@example.com",
            password="SecurePass123",
            name="New User",
            bio="Hello world"
        )
        
        # Simulate creating response after DB persistence
        player_id = uuid4()
        created_at = datetime.now(timezone.utc)
        
        response = PlayerResponse(
            id=player_id,
            email=register.email,
            name=register.name,
            bio=register.bio,
            roles=["Player"],
            email_verified=False,
            created_at=created_at,
            updated_at=created_at
        )
        
        assert response.email == register.email
        assert response.name == register.name
        assert response.bio == register.bio
    
    def test_update_preserves_none_values(self):
        """Test update schema preserves None for unspecified fields."""
        update = PlayerUpdate(name="Only Name Updated")
        
        # bio and password should be None (not updated)
        assert update.name == "Only Name Updated"
        assert update.bio is None
        assert update.password is None
