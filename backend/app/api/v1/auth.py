"""
Authentication API endpoints.

Provides:
- POST /auth/register - Player registration
- POST /auth/login - Player login and JWT token generation

Thin layer over PlayerService for HTTP-specific concerns.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.player import PlayerRegister, TokenResponse
from app.services.auth import create_access_token
from app.services.player import player_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new player account",
    description=(
        "Create a new player account with email and password. "
        "Returns a JWT access token for immediate authentication. "
        "Player receives 'Player' role by default. "
        "'TagMaster' role is added when creating first league."
    )
)
async def register(
    player_data: PlayerRegister,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    """
    Register a new player account.
    
    **Validation**:
    - Email must be valid format and unique
    - Password must be minimum 8 characters with uppercase, lowercase, and number
    - Name must be 2-255 characters
    
    **Response**:
    - Returns JWT access token
    - Token expires in 24 hours (configurable)
    - Token contains player_id, email, and roles
    
    **Errors**:
    - 400: Email already registered
    - 422: Validation error (invalid email, weak password, etc.)
    """
    try:
        # Use service layer for business logic
        new_player = await player_service.register_player(db, player_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Generate JWT token
    access_token = create_access_token(
        data={
            "sub": str(new_player.id),
            "email": new_player.email,
            "roles": new_player.roles
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        player_id=new_player.id,
        email=new_player.email,
        name=new_player.name,
        roles=new_player.roles
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    description=(
        "Authenticate with email and password to receive a JWT access token. "
        "Token must be included in Authorization header for protected endpoints: "
        "`Authorization: Bearer <token>`"
    )
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TokenResponse:
    """
    Authenticate player and generate JWT token.
    
    **OAuth2 Password Flow**:
    - Uses form data (not JSON) per OAuth2 spec
    - `username` field contains email address
    - `password` field contains password
    
    **Response**:
    - Returns JWT access token
    - Token expires in 24 hours (configurable)
    - Token contains player_id, email, and roles
    
    **Errors**:
    - 401: Invalid email or password
    - 401: Account has been deleted
    """
    # Use service layer for authentication
    player = await player_service.authenticate_player(
        db, 
        email=form_data.username,  # OAuth2 uses 'username' field
        password=form_data.password
    )
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    access_token = create_access_token(
        data={
            "sub": str(player.id),
            "email": player.email,
            "roles": player.roles
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        player_id=player.id,
        email=player.email,
        name=player.name,
        roles=player.roles
    )
