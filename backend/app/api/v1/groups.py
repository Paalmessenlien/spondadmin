"""
Groups API endpoints
"""
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.admin import Admin
from app.services.spond_service import get_spond_service, SpondService
from app.services.group_service import GroupService
from app.services.group_sync_service import GroupSyncService
from app.schemas.group import (
    GroupResponse,
    GroupListResponse,
    GroupUpdate,
    GroupSyncResult,
    GroupStats,
    GroupFilters,
)

router = APIRouter()


@router.post("/sync", response_model=GroupSyncResult)
async def sync_groups(
    force_refresh: bool = Query(False, description="Force refresh even if recently synced"),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    spond: SpondService = Depends(get_spond_service),
):
    """
    Synchronize groups from Spond API to local database
    """
    try:
        stats = await GroupSyncService.sync_groups(db, spond)

        await db.commit()

        return GroupSyncResult(
            total_fetched=stats["fetched"],
            created=stats["created"],
            updated=stats["updated"],
            errors=stats["errors"],
            sync_time=datetime.now(timezone.utc),
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync groups: {str(e)}"
        )


@router.get("/", response_model=GroupListResponse)
async def list_groups(
    search: str | None = Query(None, description="Search in name and description"),
    has_subgroups: bool | None = Query(None, description="Filter by presence of subgroups"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all groups with optional filtering
    """
    filters = GroupFilters(
        search=search,
        has_subgroups=has_subgroups,
        skip=skip,
        limit=limit,
    )

    groups, total = await GroupService.get_all(db, filters)

    return GroupListResponse(
        groups=[GroupResponse.model_validate(g) for g in groups],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/stats", response_model=GroupStats)
async def get_group_statistics(
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get group statistics
    """
    stats = await GroupService.get_statistics(db)
    return GroupStats(**stats)


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific group by ID
    """
    group = await GroupService.get_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return GroupResponse.model_validate(group)


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    update_data: GroupUpdate,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a group
    """
    group = await GroupService.update(db, group_id, update_data)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    await db.commit()
    await db.refresh(group)

    return GroupResponse.model_validate(group)
