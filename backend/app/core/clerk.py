"""
Clerk JWT verification.

Verifies Clerk-issued session tokens against Clerk's published JWKS,
caches the JWKS keys, and exposes a small helper to call Clerk's
backend API for invitation/user management.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx
import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

_jwks_client: Optional[PyJWKClient] = None


def _get_jwks_client() -> PyJWKClient:
    """Lazily construct (and cache) a JWKS client for Clerk's signing keys."""
    global _jwks_client
    if _jwks_client is None:
        if not settings.CLERK_ISSUER:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Clerk auth not configured (CLERK_ISSUER missing)",
            )
        jwks_url = f"{settings.CLERK_ISSUER.rstrip('/')}/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
    return _jwks_client


def verify_clerk_token(token: str) -> dict[str, Any]:
    """
    Verify a Clerk session JWT and return its payload.

    Raises HTTPException(401) on any failure: bad signature, expired,
    wrong issuer, wrong authorized party.
    """
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER,
            options={"verify_aud": False, "require": ["exp", "iat", "iss", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired",
                            headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Invalid token issuer",
                            headers={"WWW-Authenticate": "Bearer"})
    except PyJWKClientError as exc:
        # Token's kid doesn't match Clerk's JWKS — usually a legacy HS256
        # token, a token from a different Clerk instance, or garbage.
        logger.warning("Clerk JWKS signing-key lookup failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid token",
                            headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError as exc:
        logger.warning("Clerk token verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid token",
                            headers={"WWW-Authenticate": "Bearer"})

    azp = payload.get("azp")
    if azp and settings.CLERK_AUTHORIZED_PARTIES and azp not in settings.CLERK_AUTHORIZED_PARTIES:
        logger.warning("Clerk token azp=%r not in authorized parties", azp)
        raise HTTPException(status_code=401, detail="Unauthorized party",
                            headers={"WWW-Authenticate": "Bearer"})

    return payload


async def clerk_api(
    method: str,
    path: str,
    *,
    json: Optional[dict] = None,
    params: Optional[dict] = None,
) -> dict:
    """
    Make an authenticated call to Clerk's backend API.

    Raises HTTPException(500) if CLERK_SECRET_KEY is missing,
    or HTTPException with Clerk's status code on a non-2xx response.
    """
    if not settings.CLERK_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clerk auth not configured (CLERK_SECRET_KEY missing)",
        )
    url = f"{settings.CLERK_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.request(method, url, headers=headers, json=json, params=params)
    if response.status_code >= 400:
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}
        logger.warning("Clerk API %s %s -> %s: %s", method, path, response.status_code, body)
        raise HTTPException(
            status_code=response.status_code,
            detail=body.get("errors") or body.get("message") or "Clerk API error",
        )
    if not response.content:
        return {}
    return response.json()


async def get_clerk_user(clerk_user_id: str) -> dict:
    """Fetch a user object from Clerk by ID."""
    return await clerk_api("GET", f"users/{clerk_user_id}")


def primary_email_from_clerk_user(clerk_user: dict) -> Optional[str]:
    """Pick the primary email address out of a Clerk user object."""
    primary_id = clerk_user.get("primary_email_address_id")
    for addr in clerk_user.get("email_addresses", []) or []:
        if addr.get("id") == primary_id:
            return addr.get("email_address")
    addresses = clerk_user.get("email_addresses") or []
    if addresses:
        return addresses[0].get("email_address")
    return None
