"""
Members API endpoints
"""
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.admin import Admin
from app.services.spond_service import get_spond_service, SpondService
from app.services.member_service import MemberService
from app.services.member_sync_service import MemberSyncService
from app.schemas.member import (
    MemberResponse,
    MemberListResponse,
    MemberUpdate,
    MemberSyncResult,
    MemberStats,
    MemberFilters,
)

router = APIRouter()


@router.post("/sync", response_model=MemberSyncResult)
async def sync_members(
    group_id: str | None = Query(None, description="Sync members from specific group"),
    force_refresh: bool = Query(False, description="Force refresh even if recently synced"),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    spond: SpondService = Depends(get_spond_service),
):
    """
    Synchronize members from Spond API to local database

    Members are extracted from groups, so this will fetch all groups
    and extract their members.
    """
    try:
        stats = await MemberSyncService.sync_members(db, spond, group_id)

        await db.commit()

        return MemberSyncResult(
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
            detail=f"Failed to sync members: {str(e)}"
        )


@router.get("/", response_model=MemberListResponse)
async def list_members(
    search: str | None = Query(None, description="Search in name and email"),
    group_id: int | None = Query(None, description="Filter by group ID"),
    has_email: bool | None = Query(None, description="Filter by presence of email"),
    has_phone: bool | None = Query(None, description="Filter by presence of phone"),
    has_guardians: bool | None = Query(None, description="Filter by presence of guardians"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all members with optional filtering
    """
    filters = MemberFilters(
        search=search,
        group_id=group_id,
        has_email=has_email,
        has_phone=has_phone,
        has_guardians=has_guardians,
        skip=skip,
        limit=limit,
    )

    members, total = await MemberService.get_all(db, filters)

    return MemberListResponse(
        members=[MemberResponse.model_validate(m) for m in members],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/stats", response_model=MemberStats)
async def get_member_statistics(
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get member statistics
    """
    stats = await MemberService.get_statistics(db)
    return MemberStats(**stats)


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific member by ID
    """
    member = await MemberService.get_by_id(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    return MemberResponse.model_validate(member)


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: int,
    update_data: MemberUpdate,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a member
    """
    member = await MemberService.update(db, member_id, update_data)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.commit()
    await db.refresh(member)

    return MemberResponse.model_validate(member)
