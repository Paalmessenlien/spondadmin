"""
Public configuration endpoint - exposes non-sensitive config to frontend
"""
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/public")
async def get_public_config():
    """Return public configuration values"""
    return {
        "club_name": settings.CLUB_NAME,
    }
