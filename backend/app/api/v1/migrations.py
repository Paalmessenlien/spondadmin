"""
Migration management API endpoints
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.services.migration_service import MigrationService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status")
async def migration_status(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Get current migration status."""
    try:
        return await MigrationService.get_migration_status(db)
    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/history")
async def migration_history(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Get migration history."""
    try:
        return await MigrationService.get_migration_history(db)
    except Exception as e:
        logger.error(f"Failed to get migration history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/run")
async def run_migrations(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Run pending database migrations."""
    try:
        result = await MigrationService.run_migrations(db)
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
