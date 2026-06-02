"""
FastAPI dependencies for authentication and authorization.

Verifies a Clerk-issued RS256 session JWT against Clerk's JWKS, then
resolves it to a local ``Admin`` row. On first sign-in by a given
Clerk user, the admin row is looked up by the verified email
(fetched from Clerk's Backend API if the JWT doesn't carry it) and
``clerk_user_id`` is written so subsequent calls take the fast path.

If no admin row matches the email the request gets a 403 — this is
the invite-only enforcement point: only users an existing admin has
already added to the ``admins`` table can sign in.
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clerk import (
    get_clerk_user,
    primary_email_from_clerk_user,
    verify_clerk_token,
)
from app.db.session import get_db
from app.models.admin import Admin, UserRole
from app.services.admin_service import AdminService

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def _resolve_via_clerk(db: AsyncSession, payload: dict) -> Optional[Admin]:
    """
    Resolve a verified Clerk payload to a local Admin row.

    Linking order:
      1. Match by ``clerk_user_id`` (fast path after the first sign-in)
      2. Match by ``email`` — pulled from the JWT if present, otherwise
         from Clerk's Backend API as a fallback — and write
         ``clerk_user_id`` onto the row
      3. None → caller should 403 (invite-only)
    """
    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        return None

    admin = await AdminService.get_by_clerk_user_id(db, clerk_user_id)
    if admin is not None:
        return admin

    # Clerk's default session JWT doesn't include the user's email — so
    # look it up via the Backend API as a fallback. Token payload is the
    # cheap path; the API call only happens on the very first sign-in
    # per admin row, before clerk_user_id is written.
    email = payload.get("email") or payload.get("primary_email_address")
    if not email:
        try:
            clerk_user = await get_clerk_user(clerk_user_id)
        except Exception as e:  # noqa: BLE001
            logger.warning("Clerk get_user lookup failed for %s: %s", clerk_user_id, e)
            return None
        email = primary_email_from_clerk_user(clerk_user)
    if not email:
        return None

    admin = await AdminService.get_by_email(db, email)
    if admin is None:
        return None

    admin = await AdminService.link_clerk_user(db, admin.id, clerk_user_id)
    if admin and not admin.is_active:
        admin.is_active = True
        await db.flush()
        await db.refresh(admin)
    await db.commit()
    return admin


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    """Resolve the Clerk bearer token into an Admin row."""
    token = credentials.credentials
    payload = verify_clerk_token(token)
    admin = await _resolve_via_clerk(db, payload)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No matching admin account. Please ask an existing admin to invite you.",
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return admin


async def get_current_active_user(
    current_user: Admin = Depends(get_current_user),
) -> Admin:
    """Get the current active user (redundant guard kept for back-compat)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(*allowed_roles: UserRole):
    """Dependency factory enforcing one of the allowed roles."""
    async def role_checker(current_user: Admin = Depends(get_current_user)) -> Admin:
        if UserRole(current_user.role) not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user
    return role_checker


get_current_admin = require_role(UserRole.ADMIN)
get_current_editor_or_above = require_role(UserRole.ADMIN, UserRole.EDITOR)
get_current_superuser = get_current_admin
# Expense review (utlegg): treasurer or admin.
get_current_kasserer_or_admin = require_role(UserRole.ADMIN, UserRole.KASSERER)
