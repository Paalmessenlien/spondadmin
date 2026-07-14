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
from app.core.modules import MODULES
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.admin import (
    AdminInvite,
    AdminUpdate,
    AdminResponse,
)
from app.services.admin_service import AdminService
from app.services.access_service import AccessService

logger_auth = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=AdminResponse)
async def get_current_user_info(
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user information, including the resolved ``effective_modules``
    the frontend uses to filter navigation and gate pages.
    """
    resp = AdminResponse.model_validate(current_user)
    resp.effective_modules = sorted(
        await AccessService.resolve_effective_modules(db, current_user)
    )
    return resp


@router.get("/modules")
async def list_modules(
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    The module registry, for the admin user-management editor.

    Returns every module (key + label + sidebar group) plus the live default
    module set per role (from the editable ``role_module_defaults`` table), so
    the editor can show which boxes a role would tick by default.
    """
    role_defaults = await AccessService.get_role_defaults(db)
    return {
        "modules": [
            {"key": m.key, "label": m.label, "group": m.group} for m in MODULES
        ],
        "role_defaults": {role: sorted(keys) for role, keys in role_defaults.items()},
    }


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
    # Don't allow users to change their own superuser status, role, or
    # module access — those are privilege boundaries only an admin may set.
    if update_data.is_superuser is not None:
        update_data.is_superuser = current_user.is_superuser
    if update_data.role is not None:
        update_data.role = current_user.role
    if "modules" in update_data.model_fields_set:
        update_data.modules = current_user.modules
        update_data.model_fields_set.discard("modules")
    if "access_group_id" in update_data.model_fields_set:
        update_data.model_fields_set.discard("access_group_id")

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


def _invitation_payload(email: str, role: str, origin: str | None) -> dict:
    """Build the Clerk invitation payload, adding a login redirect when the
    request carries an Origin header."""
    payload = {
        "email_address": email,
        "public_metadata": {"role": role},
        "notify": True,
    }
    redirect_url = (str(origin or "").rstrip("/") + "/login") if origin else ""
    if redirect_url and redirect_url != "/login":
        payload["redirect_url"] = redirect_url
    return payload


async def _send_clerk_invitation(email: str, role: str, origin: str | None) -> None:
    """Create a Clerk invitation (sends the email)."""
    await clerk_api("POST", "invitations", json=_invitation_payload(email, role, origin))


async def _revoke_pending_invitations(email: str) -> None:
    """
    Revoke any existing *pending* Clerk invitations for ``email``.

    Clerk rejects creating a second pending invitation for the same address,
    so a resend must revoke the old one first. Best-effort: failures here are
    logged, not raised, so a stale/expired invite can't block a resend.
    """
    try:
        result = await clerk_api("GET", "invitations", params={"status": "pending", "limit": 100})
    except HTTPException as exc:
        logger_auth.warning("Listing Clerk invitations failed for %s: %s", email, exc.detail)
        return
    items = result.get("data") if isinstance(result, dict) else result
    for inv in (items or []):
        if inv.get("email_address") == email and inv.get("status") == "pending":
            inv_id = inv.get("id")
            if not inv_id:
                continue
            try:
                await clerk_api("POST", f"invitations/{inv_id}/revoke")
            except HTTPException as exc:
                logger_auth.warning("Revoking Clerk invitation %s failed: %s", inv_id, exc.detail)


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

    try:
        await _send_clerk_invitation(invite.email, invite.role, request.headers.get("origin"))
    except HTTPException as exc:
        await db.rollback()
        logger_auth.warning("Clerk invitation failed for %s: %s", invite.email, exc.detail)
        raise

    await db.commit()
    await db.refresh(admin)
    return admin


@router.post("/admins/{admin_id}/resend-invite", response_model=AdminResponse)
@limiter.limit("10/hour")
async def resend_invite(
    request: Request,
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Admin = Depends(get_current_superuser),
):
    """
    Re-send a Clerk invitation for a still-pending admin.

    Only valid while the user hasn't signed in yet (``is_active`` is False and
    no ``clerk_user_id`` linked). Any existing pending Clerk invitation for the
    address is revoked first, since Clerk rejects a duplicate pending invite.

    Rate limit: 10 per hour per IP.
    """
    admin = await AdminService.get_by_id(db, admin_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    if admin.clerk_user_id or admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user has already signed in — there's no pending invite to resend.",
        )

    await _revoke_pending_invitations(admin.email)
    try:
        await _send_clerk_invitation(admin.email, admin.role or "viewer", request.headers.get("origin"))
    except HTTPException as exc:
        logger_auth.warning("Resend invitation failed for %s: %s", admin.email, exc.detail)
        raise
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
        # Group assignment is applied after the base update. Assigning a group
        # copies its role onto the user and clears per-user module overrides,
        # so it takes precedence over any role/modules in the same request.
        if "access_group_id" in update_data.model_fields_set:
            await AccessService.assign_group(db, admin, update_data.access_group_id)
            await db.flush()
        await db.commit()
        await db.refresh(admin)
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
