"""API Version 1 Routers"""

from fastapi import APIRouter

from app.api.v1 import auth, health, players

api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(players.router)
api_router.include_router(health.router)

__all__ = ["api_router"]
