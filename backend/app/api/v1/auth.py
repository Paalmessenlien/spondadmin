"""
Authentication API endpoints.

Identity is owned by Clerk. The legacy ``/login`` and ``/refresh``
routes have been removed — sign-in happens at the Clerk hosted page
and the frontend supplies Clerk's session JWT as a bearer token.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.clerk import clerk_api
from app.core.deps import get_current_user, get_current_superuser, get_current_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.admin import (
    AdminInvite,
    AdminUpdate,
    AdminResponse,
)
from app.services.admin_service import AdminService

logger_auth = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=AdminResponse)
async def get_current_user_info(
    current_user: Admin = Depends(get_current_user),
):
    """
    Get current user information

    Args:
        current_user: Current authenticated user

    Returns:
        Current user data
    """
    return current_user


@router.put("/me", response_model=AdminResponse)
async def update_current_user(
    update_data: AdminUpdate,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user information

    Args:
        update_data: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException: If update fails
    """
    # Don't allow users to change their own superuser status or role
    if update_data.is_superuser is not None:
        update_data.is_superuser = current_user.is_superuser
    if update_data.role is not None:
        update_data.role = current_user.role

    try:
        updated_admin = await AdminService.update(db, current_user.id, update_data)
        if not updated_admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        await db.commit()
        return updated_admin
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/invite", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def invite_admin(
    request: Request,
    invite: AdminInvite,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    Invite a new admin via Clerk.

    Creates a pending ``admins`` row (is_active=False, no
    clerk_user_id yet) and issues a Clerk invitation email. The user
    is auto-linked + activated on their first successful Clerk
    sign-in (see ``deps._resolve_via_clerk``).

    Rate limit: 10 invitations per hour per IP.
    """
    try:
        admin = await AdminService.create_invited(db, invite)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    redirect_url = str(request.headers.get("origin") or "").rstrip("/") + "/login"
    payload = {
        "email_address": invite.email,
        "public_metadata": {"role": invite.role},
        "notify": True,
    }
    if redirect_url and redirect_url != "/login":
        payload["redirect_url"] = redirect_url

    try:
        await clerk_api("POST", "invitations", json=payload)
    except HTTPException as exc:
        await db.rollback()
        logger_auth.warning("Clerk invitation failed for %s: %s", invite.email, exc.detail)
        raise

    await db.commit()
    await db.refresh(admin)
    return admin


@router.get("/admins", response_model=List[AdminResponse])
async def list_admins(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    List all admins (superuser only)

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current superuser

    Returns:
        List of admins
    """
    admins = await AdminService.get_all(db, skip=skip, limit=limit)
    return admins


@router.get("/admins/{admin_id}", response_model=AdminResponse)
async def get_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    Get a specific admin by ID (superuser only)

    Args:
        admin_id: Admin ID
        db: Database session
        current_user: Current superuser

    Returns:
        Admin data

    Raises:
        HTTPException: If admin not found
    """
    admin = await AdminService.get_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    return admin


@router.put("/admins/{admin_id}", response_model=AdminResponse)
async def update_admin(
    admin_id: int,
    update_data: AdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    Update an admin (superuser only)

    Args:
        admin_id: Admin ID
        update_data: Update data
        db: Database session
        current_user: Current superuser

    Returns:
        Updated admin data

    Raises:
        HTTPException: If update fails
    """
    try:
        admin = await AdminService.update(db, admin_id, update_data)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        await db.commit()
        return admin
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    Delete an admin (superuser only)

    Args:
        admin_id: Admin ID
        db: Database session
        current_user: Current superuser

    Raises:
        HTTPException: If admin not found or cannot delete self
    """
    # Prevent deleting self
    if admin_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    admin = await AdminService.get_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )

    clerk_user_id = admin.clerk_user_id
    await AdminService.delete(db, admin_id)
    await db.commit()

    if clerk_user_id and settings.CLERK_SECRET_KEY:
        try:
            await clerk_api("DELETE", f"users/{clerk_user_id}")
        except HTTPException as exc:
            logger_auth.warning(
                "Clerk user %s delete failed (local row already removed): %s",
                clerk_user_id, exc.detail,
            )
