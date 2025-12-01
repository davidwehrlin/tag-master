"""
Pytest configuration and shared fixtures for all tests.

Provides async database session, test client, and authenticated user factory.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
from datetime import datetime, timezone


@pytest.fixture
def db_session():
    """
    Provide a mock async database session for testing.
    
    Uses mocks instead of real database to isolate unit tests.
    """
    db = AsyncMock()
    db.add = Mock()  # make synchronous for side_effect capture
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def test_client():
    """
    Provide a test HTTP client for API contract tests.
    
    Lazy-loaded to avoid importing app on conftest load.
    """
    try:
        from httpx import AsyncClient
        from app.main import app
        
        async def _get_client():
            async with AsyncClient(app=app, base_url="http://test") as client:
                yield client
        
        return _get_client()
    except ImportError:
        # If app cannot be imported, return None for contract tests to skip
        return None


@pytest.fixture
def sample_player_data():
    """
    Provide sample player data for testing.
    
    Contains valid player attributes.
    """
    return {
        "id": uuid4(),
        "email": "testplayer@example.com",
        "password_hash": "$2b$12$hashed_test_password",
        "name": "Test Player",
        "bio": "Test player bio",
        "roles": ["Player"],
        "email_verified": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "deleted_at": None,
    }


@pytest.fixture
def authenticated_user_factory():
    """
    Factory fixture for creating authenticated user mock objects.
    
    Returns a callable that creates player mock objects with optional role assignments.
    """
    def factory(
        email="auth@example.com",
        name="Authenticated User",
        roles=None,
        player_id=None,
    ):
        """
        Create an authenticated user mock.
        
        Args:
            email: User email address
            name: User display name
            roles: List of role strings (defaults to ["Player"])
            player_id: UUID of the player (auto-generated if not provided)
        
        Returns:
            Mock player object with authentication attributes
        """
        if roles is None:
            roles = ["Player"]
        
        if player_id is None:
            player_id = uuid4()
        
        player = Mock()
        player.id = player_id
        player.email = email
        player.name = name
        player.password_hash = "$2b$12$hashed_test_password"
        player.bio = "User bio"
        player.roles = roles
        player.email_verified = True
        player.deleted_at = None
        player.created_at = datetime.now(timezone.utc)
        player.updated_at = datetime.now(timezone.utc)
        
        # Mock methods used by service layer
        player.has_role = Mock(
            side_effect=lambda role: role in roles
        )
        player.add_role = Mock(side_effect=lambda role: roles.append(role) if role not in roles else None)
        player.soft_delete = Mock()
        
        return player
    
    return factory


@pytest.fixture
def jwt_token_factory():
    """
    Factory fixture for creating JWT tokens for authenticated requests.
    
    Returns a callable that creates valid JWT tokens for testing.
    """
    def factory(player_id=None, email="testuser@example.com"):
        """
        Create a JWT token.
        
        Args:
            player_id: UUID of the player (auto-generated if not provided)
            email: Email to encode in the token
        
        Returns:
            JWT token string
        """
        if player_id is None:
            player_id = uuid4()
        
        try:
            from app.services.auth import create_jwt_token
            return create_jwt_token(player_id, email)
        except ImportError:
            # Return a fake token if auth service cannot be imported
            return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.token"
    
    return factory


@pytest.fixture
def mock_db_for_queries():
    """
    Provide a mock database session configured for query operations.
    
    Pre-configured with common query response patterns.
    """
    db = AsyncMock()
    db.add = Mock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    
    # Configure default execute behavior
    result = Mock()
    result.scalar_one_or_none = Mock(return_value=None)
    result.scalar_one = Mock(return_value=0)
    result.scalars = Mock(return_value=Mock(all=Mock(return_value=[])))
    db.execute.return_value = result
    
    return db


@pytest.fixture
def mock_auth_service():
    """
    Provide a mock auth service for testing authentication flows.
    
    Mocks password verification and JWT operations.
    """
    with patch("app.services.auth.hash_password") as mock_hash, \
         patch("app.services.auth.verify_password") as mock_verify, \
         patch("app.services.auth.create_jwt_token") as mock_jwt:
        
        mock_hash.return_value = "$2b$12$hashed_password_here"
        mock_verify.return_value = True
        mock_jwt.return_value = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        
        yield {
            "hash_password": mock_hash,
            "verify_password": mock_verify,
            "create_jwt_token": mock_jwt,
        }


@pytest.fixture
def auth_headers(jwt_token_factory):
    """
    Provide standard Authorization headers for API requests.
    
    Returns headers dict with Bearer token for authenticated requests.
    """
    token = jwt_token_factory()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def pagination_params():
    """
    Provide common pagination parameters for list endpoint testing.
    
    Returns dict with standard page and size values.
    """
    return {
        "page": 1,
        "size": 20,
    }
