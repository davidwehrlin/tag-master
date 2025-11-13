"""
Unit tests for authentication service.

Tests verify:
- Password hashing and verification
- JWT token creation and verification
- Token expiration handling
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import jwt

from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    get_token_payload,
)


class TestPasswordHashing:
    """Test password hashing utilities."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "mySecureP@ss123"
        hashed = hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_for_same_input(self):
        """Test that hashing the same password twice produces different hashes (salt)."""
        password = "mySecureP@ss123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2

    def test_hash_password_uses_bcrypt(self):
        """Test that hash uses bcrypt format."""
        password = "mySecureP@ss123"
        hashed = hash_password(password)
        
        # Bcrypt hashes start with $2b$ or $2a$
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        password = "mySecureP@ss123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password."""
        password = "mySecureP@ss123"
        wrong_password = "wrongPassword"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_string(self):
        """Test that verify_password handles empty strings."""
        password = "mySecureP@ss123"
        hashed = hash_password(password)
        
        assert verify_password("", hashed) is False

    def test_hash_password_handles_special_characters(self):
        """Test that password hashing works with special characters."""
        password = "p@$$w0rd!#%&*()[]{}|<>?"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True


class TestJWTTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string."""
        data = {"sub": "user123", "email": "user@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_has_three_parts(self):
        """Test that JWT token has three parts (header.payload.signature)."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_token_includes_data(self):
        """Test that token includes the provided data."""
        data = {"sub": "user123", "email": "user@example.com", "roles": ["Player"]}
        token = create_access_token(data)
        
        # Decode without verification to check payload
        payload = get_token_payload(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"
        assert payload["roles"] == ["Player"]

    def test_create_access_token_includes_expiration(self):
        """Test that token includes expiration claim."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        payload = get_token_payload(token)
        assert "exp" in payload
        assert isinstance(payload["exp"], int)

    def test_create_access_token_custom_expiration(self):
        """Test that custom expiration time is respected."""
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=2)
        
        before = datetime.now(timezone.utc)
        token = create_access_token(data, expires_delta)
        after = datetime.now(timezone.utc)
        
        payload = get_token_payload(token)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        # Expiration should be roughly 2 hours from now (within a few seconds)
        expected_min = before + expires_delta - timedelta(seconds=1)
        expected_max = after + expires_delta + timedelta(seconds=5)
        assert expected_min <= exp_time <= expected_max

    def test_create_access_token_default_expiration(self):
        """Test that default expiration is used when not specified."""
        data = {"sub": "user123"}
        
        with patch("app.services.auth.settings.jwt_access_token_expire_minutes", 1440):  # 24 hours
            before = datetime.now(timezone.utc)
            token = create_access_token(data)
            after = datetime.now(timezone.utc)
            
            payload = get_token_payload(token)
            exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            
            # Expiration should be roughly 24 hours from now (within a few seconds)
            expected_min = before + timedelta(minutes=1440) - timedelta(seconds=1)
            expected_max = after + timedelta(minutes=1440) + timedelta(seconds=5)
            assert expected_min <= exp_time <= expected_max

    def test_create_access_token_does_not_modify_input(self):
        """Test that creating token doesn't modify the input dictionary."""
        data = {"sub": "user123", "email": "user@example.com"}
        original_data = data.copy()
        
        create_access_token(data)
        
        assert data == original_data


class TestJWTTokenDecoding:
    """Test JWT token decoding and verification."""

    def test_decode_access_token_valid(self):
        """Test that decode_access_token decodes valid tokens."""
        data = {"sub": "user123", "email": "user@example.com"}
        token = create_access_token(data)
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"

    def test_decode_access_token_invalid_signature(self):
        """Test that decode_access_token returns None for invalid signature."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        # Tamper with the token
        parts = token.split(".")
        parts[2] = "invalidsignature"
        tampered_token = ".".join(parts)
        
        payload = decode_access_token(tampered_token)
        
        assert payload is None

    def test_decode_access_token_expired(self):
        """Test that decode_access_token returns None for expired tokens."""
        data = {"sub": "user123"}
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        payload = decode_access_token(token)
        
        assert payload is None

    def test_decode_access_token_malformed(self):
        """Test that decode_access_token returns None for malformed tokens."""
        malformed_tokens = [
            "notavalidtoken",
            "header.payload",  # Missing signature
            "too.many.parts.here",
            "",
            "header..signature",  # Empty payload
        ]
        
        for token in malformed_tokens:
            payload = decode_access_token(token)
            assert payload is None, f"Expected None for token: {token}"

    def test_decode_access_token_wrong_algorithm(self):
        """Test that token signed with different algorithm is rejected."""
        data = {"sub": "user123"}
        
        # Create token with different algorithm
        with patch("app.services.auth.settings.jwt_secret_key", "test_secret"):
            with patch("app.services.auth.settings.jwt_algorithm", "HS256"):
                token = jwt.encode(
                    {**data, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                    "test_secret",
                    algorithm="HS512"  # Different algorithm
                )
        
        # Try to decode with HS256 (should fail)
        payload = decode_access_token(token)
        assert payload is None


class TestGetTokenPayload:
    """Test unverified token payload extraction."""

    def test_get_token_payload_returns_payload(self):
        """Test that get_token_payload returns payload without verification."""
        data = {"sub": "user123", "email": "user@example.com"}
        token = create_access_token(data)
        
        payload = get_token_payload(token)
        
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"

    def test_get_token_payload_expired_token(self):
        """Test that get_token_payload returns payload even for expired tokens."""
        data = {"sub": "user123"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        payload = get_token_payload(token)
        
        # Should still return payload (no verification)
        assert payload is not None
        assert payload["sub"] == "user123"

    def test_get_token_payload_invalid_signature(self):
        """Test that get_token_payload returns payload even with invalid signature."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        # Tamper with signature
        parts = token.split(".")
        parts[2] = "invalidsignature"
        tampered_token = ".".join(parts)
        
        payload = get_token_payload(tampered_token)
        
        # Should still return payload (no signature verification)
        assert payload is not None
        assert payload["sub"] == "user123"

    def test_get_token_payload_malformed(self):
        """Test that get_token_payload returns None for malformed tokens."""
        malformed_tokens = [
            "notavalidtoken",
            "",
            "invalid",
        ]
        
        for token in malformed_tokens:
            payload = get_token_payload(token)
            assert payload is None, f"Expected None for token: {token}"


class TestPasswordHashingIntegration:
    """Integration tests for password hashing workflow."""

    def test_full_password_workflow(self):
        """Test complete password hashing and verification workflow."""
        # User registration: hash password
        plain_password = "mySecurePassword123!"
        hashed = hash_password(plain_password)
        
        # Store hashed password in database (simulated)
        stored_password_hash = hashed
        
        # User login: verify password
        login_attempt = "mySecurePassword123!"
        is_valid = verify_password(login_attempt, stored_password_hash)
        
        assert is_valid is True
        
        # Wrong password attempt
        wrong_attempt = "wrongPassword"
        is_valid = verify_password(wrong_attempt, stored_password_hash)
        
        assert is_valid is False

    def test_multiple_users_different_hashes(self):
        """Test that same password for different users produces different hashes."""
        password = "commonPassword123"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        hash3 = hash_password(password)
        
        # All hashes should be different (different salts)
        assert hash1 != hash2
        assert hash2 != hash3
        assert hash1 != hash3
        
        # But all should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
        assert verify_password(password, hash3)


class TestJWTIntegration:
    """Integration tests for JWT token workflow."""

    def test_full_jwt_workflow(self):
        """Test complete JWT creation and verification workflow."""
        # User logs in: create token
        user_data = {
            "sub": "user123",
            "email": "user@example.com",
            "roles": ["Player"]
        }
        token = create_access_token(user_data)
        
        # User makes authenticated request: verify token
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"
        assert payload["roles"] == ["Player"]

    def test_token_refresh_workflow(self):
        """Test token refresh with new expiration."""
        # Create initial token
        data = {"sub": "user123"}
        token1 = create_access_token(data, expires_delta=timedelta(minutes=15))
        
        # Extract user data from token
        payload = decode_access_token(token1)
        
        # Create new token with fresh expiration
        token2 = create_access_token(
            {"sub": payload["sub"]},
            expires_delta=timedelta(hours=24)
        )
        
        # Both tokens should be valid
        assert decode_access_token(token1) is not None
        assert decode_access_token(token2) is not None
        
        # But they should be different tokens
        assert token1 != token2
