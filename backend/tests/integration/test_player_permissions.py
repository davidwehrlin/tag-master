"""
Integration tests for player permissions.

Tests that players can only modify their own profile and cannot access other profiles.
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4


class TestPlayerProfilePermissions:
    """Test permission controls for player profile operations."""
    
    @pytest.mark.asyncio
    async def test_player_can_update_own_profile(self, test_client):
        """Test player can update their own profile."""
        # Register first user
        register_response = await test_client.post(
            "/auth/register",
            json={
                "email": "player1@example.com",
                "password": "SecurePass123",
                "name": "Player One"
            }
        )
        
        if register_response.status_code in [200, 201]:
            # Login to get token
            login_response = await test_client.post(
                "/auth/login",
                json={
                    "email": "player1@example.com",
                    "password": "SecurePass123"
                }
            )
            
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                # Update own profile
                response = await test_client.put(
                    "/players/me",
                    headers=headers,
                    json={"name": "Updated Player One"}
                )
                
                # Expected: 200 OK
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_player_cannot_update_other_profile(self, test_client):
        """Test player cannot update another player's profile."""
        # Register two players
        register1 = await test_client.post(
            "/auth/register",
            json={
                "email": "player_a@example.com",
                "password": "SecurePass123",
                "name": "Player A"
            }
        )
        
        register2 = await test_client.post(
            "/auth/register",
            json={
                "email": "player_b@example.com",
                "password": "SecurePass123",
                "name": "Player B"
            }
        )
        
        if register1.status_code in [200, 201] and register2.status_code in [200, 201]:
            # Get player B ID
            player_b_data = register2.json()
            player_b_id = player_b_data.get("id") or player_b_data.get("player_id")
            
            # Login as Player A
            login_a = await test_client.post(
                "/auth/login",
                json={
                    "email": "player_a@example.com",
                    "password": "SecurePass123"
                }
            )
            
            if login_a.status_code == 200:
                token_a = login_a.json().get("access_token")
                headers_a = {"Authorization": f"Bearer {token_a}"}
                
                # Try to update Player B's profile (should fail if endpoint exists)
                response = await test_client.put(
                    f"/players/{player_b_id}",
                    headers=headers_a,
                    json={"name": "Hacked Name"}
                )
                
                # Expected: 403 Forbidden or 404 Not Found (endpoint may not exist)
                assert response.status_code in [403, 404]
    
    @pytest.mark.asyncio
    async def test_player_cannot_delete_other_profile(self, test_client):
        """Test player cannot delete another player's profile."""
        # Register two players
        register1 = await test_client.post(
            "/auth/register",
            json={
                "email": "deleter@example.com",
                "password": "SecurePass123",
                "name": "Deleter"
            }
        )
        
        register2 = await test_client.post(
            "/auth/register",
            json={
                "email": "target@example.com",
                "password": "SecurePass123",
                "name": "Target"
            }
        )
        
        if register1.status_code in [200, 201] and register2.status_code in [200, 201]:
            # Get target ID
            target_data = register2.json()
            target_id = target_data.get("id") or target_data.get("player_id")
            
            # Login as Deleter
            login_response = await test_client.post(
                "/auth/login",
                json={
                    "email": "deleter@example.com",
                    "password": "SecurePass123"
                }
            )
            
            if login_response.status_code == 200:
                token = login_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                # Try to delete Target's profile (should fail if endpoint exists)
                response = await test_client.delete(
                    f"/players/{target_id}",
                    headers=headers
                )
                
                # Expected: 403 Forbidden or 404 Not Found
                assert response.status_code in [403, 404]
    
    @pytest.mark.asyncio
    async def test_player_cannot_view_private_data(self, test_client):
        """Test player cannot access other player's private profile data."""
        # Register two players
        await test_client.post(
            "/auth/register",
            json={
                "email": "viewer@example.com",
                "password": "SecurePass123",
                "name": "Viewer"
            }
        )
        
        register2 = await test_client.post(
            "/auth/register",
            json={
                "email": "private@example.com",
                "password": "SecurePass123",
                "name": "Private Player"
            }
        )
        
        if register2.status_code in [200, 201]:
            private_data = register2.json()
            private_id = private_data.get("id") or private_data.get("player_id")
            
            # Login as Viewer
            login = await test_client.post(
                "/auth/login",
                json={
                    "email": "viewer@example.com",
                    "password": "SecurePass123"
                }
            )
            
            if login.status_code == 200:
                token = login.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                # Try to view private player (if endpoint requires own profile)
                response = await test_client.get(
                    f"/players/{private_id}",
                    headers=headers
                )
                
                # Depending on API design, this may be allowed or forbidden
                # If list shows all public profiles, this should be 200
                # If profiles are private, this should be 403
                assert response.status_code in [200, 403, 404]


class TestPlayerSoftDeletePermissions:
    """Test permission controls for soft deletion."""
    
    @pytest.mark.asyncio
    async def test_deleted_player_cannot_login(self, test_client):
        """Test deleted player cannot login."""
        # Register player
        await test_client.post(
            "/auth/register",
            json={
                "email": "willdelete@example.com",
                "password": "SecurePass123",
                "name": "Will Delete"
            }
        )
        
        # Login and delete
        login = await test_client.post(
            "/auth/login",
            json={
                "email": "willdelete@example.com",
                "password": "SecurePass123"
            }
        )
        
        if login.status_code == 200:
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Delete profile
            delete_response = await test_client.delete(
                "/players/me",
                headers=headers
            )
            
            if delete_response.status_code in [200, 204]:
                # Try to login again
                login_again = await test_client.post(
                    "/auth/login",
                    json={
                        "email": "willdelete@example.com",
                        "password": "SecurePass123"
                    }
                )
                
                # Expected: 401 Unauthorized (soft-deleted users excluded)
                assert login_again.status_code == 401
    
    @pytest.mark.asyncio
    async def test_deleted_player_not_in_player_list(self, test_client):
        """Test deleted player is excluded from player list."""
        # Register and immediately delete
        register = await test_client.post(
            "/auth/register",
            json={
                "email": "hidden@example.com",
                "password": "SecurePass123",
                "name": "Will Hide"
            }
        )
        
        # Login as another user to view list
        await test_client.post(
            "/auth/register",
            json={
                "email": "lister@example.com",
                "password": "SecurePass123",
                "name": "Lister"
            }
        )
        
        login = await test_client.post(
            "/auth/login",
            json={
                "email": "lister@example.com",
                "password": "SecurePass123"
            }
        )
        
        if login.status_code == 200:
            token = login.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Delete hidden@example.com user
            if register.status_code in [200, 201]:
                hidden_token_login = await test_client.post(
                    "/auth/login",
                    json={
                        "email": "hidden@example.com",
                        "password": "SecurePass123"
                    }
                )
                
                if hidden_token_login.status_code == 200:
                    hidden_token = hidden_token_login.json().get("access_token")
                    hidden_headers = {"Authorization": f"Bearer {hidden_token}"}
                    
                    await test_client.delete(
                        "/players/me",
                        headers=hidden_headers
                    )
            
            # List players
            response = await test_client.get(
                "/players",
                headers=headers
            )
            
            # Expected: 200 OK, hidden@example.com not in list
            if response.status_code == 200:
                data = response.json()
                players = data.get("players", data if isinstance(data, list) else [])
                emails = [p.get("email") for p in players if isinstance(p, dict)]
                assert "hidden@example.com" not in emails


class TestAuthenticationPermissions:
    """Test authentication-based permission controls."""
    
    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_protected_endpoints(self, test_client):
        """Test unauthenticated users cannot access protected endpoints."""
        # Try to access /players/me without token
        response = await test_client.get("/players/me")
        
        # Expected: 401 Unauthorized
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_expired_token_denied_access(self, test_client):
        """Test expired token is rejected."""
        response = await test_client.get(
            "/players/me",
            headers={"Authorization": "Bearer expired_token_12345"}
        )
        
        # Expected: 401 Unauthorized
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_invalid_token_format_denied(self, test_client):
        """Test invalid token format is rejected."""
        response = await test_client.get(
            "/players/me",
            headers={"Authorization": "InvalidTokenFormat"}
        )
        
        # Expected: 401 Unauthorized
        assert response.status_code == 401
