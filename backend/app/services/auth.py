"""
Authentication services for password hashing and JWT token management.

Provides utilities for:
- Password hashing with bcrypt
- JWT token creation and verification
- Token payload extraction
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext

from app.config import settings

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    
    Args:
        password: Plain-text password to hash
        
    Returns:
        Hashed password string
        
    Example:
        hashed = hash_password("mySecureP@ss123")
        # Returns: "$2b$12$..."
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a hashed password.
    
    Args:
        plain_password: Plain-text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        is_valid = verify_password("mySecureP@ss123", user.password_hash)
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with optional expiration.
    
    Args:
        data: Dictionary of claims to encode in the token (e.g., {"sub": user_id, "email": email, "roles": ["Player"]})
        expires_delta: Optional custom expiration time delta
        
    Returns:
        Encoded JWT token string
        
    Example:
        token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "roles": user.roles}
        )
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Dictionary of token claims if valid, None if invalid/expired
        
    Example:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")
            email = payload.get("email")
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except PyJWTError:
        return None


def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract payload from JWT token without verification.
    
    WARNING: This does NOT verify the token signature. Only use for debugging
    or when token has already been verified.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary of token claims (unverified), None if decode fails
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except PyJWTError:
        return None
