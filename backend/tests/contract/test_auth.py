"""
Contract tests for authentication endpoints.

Tests registration, login, invalid credentials, and duplicate email scenarios.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestAuthRegistrationEndpoint:
    """Test POST /auth/register endpoint."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, test_client):
        """Test successful player registration."""
        response = await test_client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "name": "New User",
                "bio": "User bio"
            }
        )
        
        # Expected: 201 Created with player data
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or "player_id" in data
        assert data.get("email") == "newuser@example.com" or "newuser@example.com" in str(data)
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, test_client):
        """Test registration fails with duplicate email."""
        # First registration
        await test_client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123",
                "name": "First User"
            }
        )
        
        # Second registration with same email
        response = await test_client.post(
            "/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "SecurePass123",
                "name": "Second User"
            }
        )
        
        # Expected: 409 Conflict or 422 Unprocessable Entity
        assert response.status_code in [409, 422, 400]
        assert "already registered" in response.json().get("detail", "").lower() or \
               "duplicate" in response.json().get("detail", "").lower()
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, test_client):
        """Test registration fails with invalid email format."""
        response = await test_client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123",
                "name": "Test User"
            }
        )
        
        # Expected: 422 Unprocessable Entity
        assert response.status_code == 422
        assert "email" in response.json().get("detail", "").lower() or \
               "invalid" in response.json().get("detail", "").lower()
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, test_client):
        """Test registration fails with weak password."""
        response = await test_client.post(
            "/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "name": "Test User"
            }
        )
        
        # Expected: 422 Unprocessable Entity
        assert response.status_code == 422
        assert "password" in response.json().get("detail", "").lower()
    
    @pytest.mark.asyncio
    async def test_register_missing_required_field(self, test_client):
        """Test registration fails without required fields."""
        response = await test_client.post(
            "/auth/register",
            json={
                "email": "incomplete@example.com",
                # Missing password and name
            }
        )
        
        # Expected: 422 Unprocessable Entity
        assert response.status_code == 422


class TestAuthLoginEndpoint:
    """Test POST /auth/login endpoint."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, test_client):
        """Test successful login returns JWT token."""
        # First register a user
        await test_client.post(
            "/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123",
                "name": "Login User"
            }
        )
        
        # Then login
        response = await test_client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123"
            }
        )
        
        # Expected: 200 OK with token
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
        assert data.get("token_type", "").lower() == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_invalid_email(self, test_client):
        """Test login fails with non-existent email."""
        response = await test_client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SecurePass123"
            }
        )
        
        # Expected: 401 Unauthorized
        assert response.status_code == 401
        assert "invalid" in response.json().get("detail", "").lower() or \
               "credentials" in response.json().get("detail", "").lower()
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, test_client):
        """Test login fails with incorrect password."""
        # Register a user
        await test_client.post(
            "/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "SecurePass123",
                "name": "Wrong Pass User"
            }
        )
        
        # Login with wrong password
        response = await test_client.post(
            "/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPassword123"
            }
        )
        
        # Expected: 401 Unauthorized
        assert response.status_code == 401
        assert "invalid" in response.json().get("detail", "").lower() or \
               "credentials" in response.json().get("detail", "").lower()
    
    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, test_client):
        """Test login fails without email or password."""
        response = await test_client.post(
            "/auth/login",
            json={
                "email": "test@example.com"
                # Missing password
            }
        )
        
        # Expected: 422 Unprocessable Entity
        assert response.status_code == 422


class TestAuthResponseStructure:
    """Test response structure of auth endpoints."""
    
    @pytest.mark.asyncio
    async def test_registration_response_structure(self, test_client):
        """Test registration response has correct structure."""
        response = await test_client.post(
            "/auth/register",
            json={
                "email": "structure@example.com",
                "password": "SecurePass123",
                "name": "Structure Test"
            }
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            # Should contain player info or token
            assert "id" in data or "player_id" in data or "access_token" in data
    
    @pytest.mark.asyncio
    async def test_login_response_structure(self, test_client):
        """Test login response has correct structure."""
        # Register first
        await test_client.post(
            "/auth/register",
            json={
                "email": "tokentest@example.com",
                "password": "SecurePass123",
                "name": "Token Test"
            }
        )
        
        # Login
        response = await test_client.post(
            "/auth/login",
            json={
                "email": "tokentest@example.com",
                "password": "SecurePass123"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
