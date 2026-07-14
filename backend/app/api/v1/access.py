"""
Access administration endpoints: reusable access groups and editable
per-role default module sets. All routes are superuser-only.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_superuser
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.access import (
    AccessGroupCreate,
    AccessGroupUpdate,
    AccessGroupResponse,
    RoleDefaultResponse,
    RoleDefaultUpdate,
)
from app.services.access_service import AccessService, EDITABLE_DEFAULT_ROLES

router = APIRouter()


async def _group_response(db: AsyncSession, group) -> AccessGroupResponse:
    resp = AccessGroupResponse.model_validate(group)
    resp.member_count = await AccessService.count_members(db, group.id)
    return resp


# ---- access groups ------------------------------------------------------
@router.get("/groups", response_model=List[AccessGroupResponse])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_superuser),
):
    groups = await AccessService.list_groups(db)
    return [await _group_response(db, g) for g in groups]


@router.post("/groups", response_model=AccessGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: AccessGroupCreate,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_superuser),
):
    try:
        group = await AccessService.create_group(
            db, name=data.name, description=data.description,
            role=data.role, modules=data.modules,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    await db.commit()
    return await _group_response(db, group)


@router.get("/groups/{group_id}", response_model=AccessGroupResponse)
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_superuser),
):
    group = await AccessService.get_group(db, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access group not found")
    return await _group_response(db, group)


@router.put("/groups/{group_id}", response_model=AccessGroupResponse)
async def update_group(
    group_id: int,
    data: AccessGroupUpdate,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_superuser),
):
    try:
        group = await AccessService.update_group(
            db, group_id,
            name=data.name, description=data.description,
            role=data.role, modules=data.modules,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access group not found")
    await db.commit()
    return await _group_response(db, group)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_superuser),
):
    deleted = await AccessService.delete_group(db, group_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access group not found")
    await db.commit()


# ---- role defaults ------------------------------------------------------
@router.get("/roles", response_model=List[RoleDefaultResponse])
async def list_role_defaults(
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_superuser),
):
    """The editable per-role default module sets (admin is always all modules)."""
    defaults = await AccessService.get_role_defaults(db)
    return [
        RoleDefaultResponse(role=role, modules=sorted(defaults.get(role, [])))
        for role in EDITABLE_DEFAULT_ROLES
    ]


@router.put("/roles/{role}", response_model=RoleDefaultResponse)
async def update_role_default(
    role: str,
    data: RoleDefaultUpdate,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_superuser),
):
    try:
        row = await AccessService.set_role_default(db, role, data.modules)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    await db.commit()
    return RoleDefaultResponse(role=row.role, modules=sorted(row.modules or []))
