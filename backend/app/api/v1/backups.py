"""
Backup management API endpoints
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.backup import BackupCreateRequest, BackupResponse, BackupListResponse
from app.services.backup_service import BackupService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=BackupResponse)
async def create_backup(
    request: BackupCreateRequest = BackupCreateRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Create a new database backup."""
    try:
        backup = await BackupService.create_backup(
            db,
            backup_type=request.backup_type,
            created_by=current_user.id,
        )
        return backup
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {str(e)}",
        )


@router.get("/", response_model=BackupListResponse)
async def list_backups(
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """List all backups."""
    backups = await BackupService.list_backups(db)
    return BackupListResponse(backups=backups, total=len(backups))


@router.get("/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Get backup details."""
    backup = await BackupService.get_backup(db, backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return backup


@router.post("/{backup_id}/restore")
async def restore_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Restore database from a backup."""
    try:
        result = await BackupService.restore_from_backup(db, backup_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}",
        )


@router.post("/{backup_id}/upload-cdn", response_model=BackupResponse)
async def upload_to_cdn(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Upload a backup to Bunny CDN."""
    try:
        backup = await BackupService.upload_to_cdn(db, backup_id)
        return backup
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"CDN upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CDN upload failed: {str(e)}",
        )


@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_admin),
):
    """Delete a backup (local file + CDN + DB record)."""
    try:
        await BackupService.delete_backup(db, backup_id)
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
