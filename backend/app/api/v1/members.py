"""
Members API endpoints
"""
from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_current_admin, get_current_editor_or_above
from app.db.session import get_db
from app.models.admin import Admin
from app.services.spond_service import get_spond_service, SpondService
from app.services.member_service import MemberService
from app.services.member_sync_service import MemberSyncService
from app.services.archer_profile_service import ArcherProfileService
from app.schemas.member import (
    MemberResponse,
    MemberListResponse,
    MemberUpdate,
    MemberSyncResult,
    MemberStats,
    MemberFilters,
)
from app.schemas.archer_profile import (
    ArcherProfileCreate,
    ArcherProfileUpdate,
    ArcherProfileResponse,
)

router = APIRouter()


@router.post("/sync", response_model=MemberSyncResult)
async def sync_members(
    group_id: str | None = Query(None, description="Sync members from specific group"),
    force_refresh: bool = Query(False, description="Force refresh even if recently synced"),
    current_user: Admin = Depends(get_current_admin),
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
    group_id: str | None = Query(None, description="Filter by group spond_id"),
    subgroup_id: str | None = Query(None, description="Filter by Spond subgroup uid"),
    has_email: bool | None = Query(None, description="Filter by presence of email"),
    has_phone: bool | None = Query(None, description="Filter by presence of phone"),
    has_guardians: bool | None = Query(None, description="Filter by presence of guardians"),
    sort_by: str = Query("name", description="name | email | group_count | subgroup_count | last_synced_at"),
    sort_order: str = Query("asc", description="asc | desc"),
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
        subgroup_id=subgroup_id,
        has_email=has_email,
        has_phone=has_phone,
        has_guardians=has_guardians,
        sort_by=sort_by,
        sort_order=sort_order,
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
    group_id: str | None = Query(None, description="Filter by group spond_id"),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get member statistics
    """
    stats = await MemberService.get_statistics(db, group_id=group_id)
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
    current_user: Admin = Depends(get_current_editor_or_above),
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


# ============================================================
# Archer Profile endpoints
# ============================================================

@router.get("/{member_id}/archery-profile", response_model=ArcherProfileResponse)
async def get_archery_profile(
    member_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the archery profile for a member (looked up via spond_id)"""
    member = await MemberService.get_by_id(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    profile = await ArcherProfileService.get_by_spond_id(db, member.spond_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Archery profile not found")

    return ArcherProfileResponse.model_validate(profile)


@router.put("/{member_id}/archery-profile", response_model=ArcherProfileResponse)
async def create_or_update_archery_profile(
    member_id: int,
    data: ArcherProfileCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """Create or update the archery profile for a member (keyed by spond_id)"""
    member = await MemberService.get_by_id(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    profile = await ArcherProfileService.get_by_spond_id(db, member.spond_id)
    if profile:
        profile = await ArcherProfileService.update(
            db, profile, ArcherProfileUpdate(**data.model_dump())
        )
    else:
        profile = await ArcherProfileService.create(db, member.spond_id, data)

    await db.commit()
    await db.refresh(profile)
    return ArcherProfileResponse.model_validate(profile)


@router.delete("/{member_id}/archery-profile", status_code=204)
async def delete_archery_profile(
    member_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """Delete the archery profile for a member"""
    member = await MemberService.get_by_id(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    profile = await ArcherProfileService.get_by_spond_id(db, member.spond_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Archery profile not found")

    await ArcherProfileService.delete(db, profile)
    await db.commit()
