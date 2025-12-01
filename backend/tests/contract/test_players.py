"""
Contract tests for player endpoints.

Tests profile retrieval, update, soft delete, and list with pagination.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestPlayerProfileEndpoint:
    """Test GET /players/me endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_profile_authenticated(self, test_client, auth_headers):
        """Test retrieving authenticated user profile."""
        # Register and login first
        await test_client.post(
            "/auth/register",
            json={
                "email": "profile@example.com",
                "password": "SecurePass123",
                "name": "Profile User"
            }
        )
        
        # Get profile
        response = await test_client.get(
            "/players/me",
            headers=auth_headers
        )
        
        # Expected: 200 OK with player data
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "name" in data
    
    @pytest.mark.asyncio
    async def test_get_profile_unauthenticated(self, test_client):
        """Test retrieving profile without authentication fails."""
        response = await test_client.get("/players/me")
        
        # Expected: 401 Unauthorized
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_profile_invalid_token(self, test_client):
        """Test retrieving profile with invalid token fails."""
        response = await test_client.get(
            "/players/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Expected: 401 Unauthorized
        assert response.status_code == 401


class TestPlayerUpdateEndpoint:
    """Test PUT /players/me endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_profile_name(self, test_client, auth_headers):
        """Test updating player name."""
        # Register user
        await test_client.post(
            "/auth/register",
            json={
                "email": "update@example.com",
                "password": "SecurePass123",
                "name": "Original Name"
            }
        )
        
        # Update profile
        response = await test_client.put(
            "/players/me",
            headers=auth_headers,
            json={"name": "Updated Name"}
        )
        
        # Expected: 200 OK with updated data
        assert response.status_code == 200
        data = response.json()
        assert data.get("name") == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_update_profile_bio(self, test_client, auth_headers):
        """Test updating player bio."""
        # Register user
        await test_client.post(
            "/auth/register",
            json={
                "email": "bioupdate@example.com",
                "password": "SecurePass123",
                "name": "Bio User"
            }
        )
        
        # Update bio
        response = await test_client.put(
            "/players/me",
            headers=auth_headers,
            json={"bio": "Updated bio"}
        )
        
        # Expected: 200 OK
        assert response.status_code == 200
        data = response.json()
        assert data.get("bio") == "Updated bio"
    
    @pytest.mark.asyncio
    async def test_update_profile_password(self, test_client, auth_headers):
        """Test updating player password."""
        # Register user
        await test_client.post(
            "/auth/register",
            json={
                "email": "passupdate@example.com",
                "password": "SecurePass123",
                "name": "Pass User"
            }
        )
        
        # Update password
        response = await test_client.put(
            "/players/me",
            headers=auth_headers,
            json={"password": "NewSecurePass456"}
        )
        
        # Expected: 200 OK
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_update_profile_unauthenticated(self, test_client):
        """Test updating profile without authentication fails."""
        response = await test_client.put(
            "/players/me",
            json={"name": "Hacker"}
        )
        
        # Expected: 401 Unauthorized
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_update_profile_invalid_data(self, test_client, auth_headers):
        """Test update with invalid data is rejected."""
        # Register user
        await test_client.post(
            "/auth/register",
            json={
                "email": "invalid@example.com",
                "password": "SecurePass123",
                "name": "Invalid User"
            }
        )
        
        # Try to update with invalid password
        response = await test_client.put(
            "/players/me",
            headers=auth_headers,
            json={"password": "weak"}  # Invalid password
        )
        
        # Expected: 422 Unprocessable Entity
        assert response.status_code == 422


class TestPlayerDeleteEndpoint:
    """Test DELETE /players/me endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_profile_success(self, test_client, auth_headers):
        """Test successful profile soft deletion."""
        # Register user
        await test_client.post(
            "/auth/register",
            json={
                "email": "delete@example.com",
                "password": "SecurePass123",
                "name": "Delete User"
            }
        )
        
        # Delete profile
        response = await test_client.delete(
            "/players/me",
            headers=auth_headers
        )
        
        # Expected: 204 No Content or 200 OK
        assert response.status_code in [200, 204]
    
    @pytest.mark.asyncio
    async def test_delete_profile_unauthenticated(self, test_client):
        """Test deleting profile without authentication fails."""
        response = await test_client.delete("/players/me")
        
        # Expected: 401 Unauthorized
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_cannot_access_after_deletion(self, test_client, auth_headers):
        """Test profile is not accessible after soft deletion."""
        # Register and delete
        await test_client.post(
            "/auth/register",
            json={
                "email": "deleted@example.com",
                "password": "SecurePass123",
                "name": "Deleted User"
            }
        )
        
        await test_client.delete(
            "/players/me",
            headers=auth_headers
        )
        
        # Try to access deleted profile
        response = await test_client.get(
            "/players/me",
            headers=auth_headers
        )
        
        # Expected: 404 Not Found or 401 Unauthorized (soft-deleted)
        assert response.status_code in [404, 401]


class TestPlayerListEndpoint:
    """Test GET /players endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_players_authenticated(self, test_client, auth_headers):
        """Test listing players with authentication."""
        # Register user
        await test_client.post(
            "/auth/register",
            json={
                "email": "list@example.com",
                "password": "SecurePass123",
                "name": "List User"
            }
        )
        
        # List players
        response = await test_client.get(
            "/players",
            headers=auth_headers
        )
        
        # Expected: 200 OK with paginated list
        assert response.status_code == 200
        data = response.json()
        assert "players" in data or "items" in data or isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_list_players_pagination(self, test_client, auth_headers):
        """Test listing players with pagination parameters."""
        # Register users
        for i in range(5):
            await test_client.post(
                "/auth/register",
                json={
                    "email": f"paginated{i}@example.com",
                    "password": "SecurePass123",
                    "name": f"Paginated User {i}"
                }
            )
        
        # List with pagination
        response = await test_client.get(
            "/players?page=1&size=10",
            headers=auth_headers
        )
        
        # Expected: 200 OK
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_list_players_excludes_deleted(self, test_client, auth_headers):
        """Test listing players excludes soft-deleted users."""
        # Register and delete a user
        await test_client.post(
            "/auth/register",
            json={
                "email": "deleted_from_list@example.com",
                "password": "SecurePass123",
                "name": "Will Delete"
            }
        )
        
        await test_client.delete(
            "/players/me",
            headers=auth_headers
        )
        
        # List players
        response = await test_client.get(
            "/players",
            headers=auth_headers
        )
        
        # Expected: 200 OK, deleted user not in list
        assert response.status_code == 200
        data = response.json()
        players = data.get("players", data if isinstance(data, list) else [])
        deleted_emails = [p.get("email") for p in players if isinstance(p, dict)]
        assert "deleted_from_list@example.com" not in deleted_emails
    
    @pytest.mark.asyncio
    async def test_list_players_unauthenticated(self, test_client):
        """Test listing players without authentication fails."""
        response = await test_client.get("/players")
        
        # Expected: 401 Unauthorized
        assert response.status_code == 401


class TestPlayerGetByIdEndpoint:
    """Test GET /players/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_player_by_id(self, test_client, auth_headers):
        """Test retrieving specific player by ID."""
        # Register user to get ID
        register_response = await test_client.post(
            "/auth/register",
            json={
                "email": "byid@example.com",
                "password": "SecurePass123",
                "name": "By ID User"
            }
        )
        
        if register_response.status_code in [200, 201]:
            data = register_response.json()
            player_id = data.get("id") or data.get("player_id")
            
            if player_id:
                # Get player by ID
                response = await test_client.get(
                    f"/players/{player_id}",
                    headers=auth_headers
                )
                
                # Expected: 200 OK
                assert response.status_code == 200
                assert response.json().get("id") == str(player_id) or response.json().get("id") == player_id
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_player(self, test_client, auth_headers):
        """Test retrieving non-existent player returns 404."""
        fake_id = uuid4()
        
        response = await test_client.get(
            f"/players/{fake_id}",
            headers=auth_headers
        )
        
        # Expected: 404 Not Found
        assert response.status_code == 404
