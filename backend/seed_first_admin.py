#!/usr/bin/env python3
"""
Idempotent bootstrap of the first administrator on a fresh environment.

What it does (in this order):

1. Connects to the local DB via ``DATABASE_URL`` and ensures an
   ``admins`` row exists for the given email with ``role=admin``
   (or the role supplied via ``--role``) and ``is_active=True``.

2. Calls Clerk's Backend API (using ``CLERK_SECRET_KEY``) to ensure a
   Clerk user exists for the same email, with the address marked as
   verified. The user is created with ``skip_password_requirement=true``
   so the operator can choose their sign-in method (Google / magic
   link / password) on first sign-in.

3. The local row's ``clerk_user_id`` is filled in **lazily** on first
   sign-in by ``deps._resolve_via_clerk`` (linking by verified email).
   This script does *not* try to write ``clerk_user_id`` itself because
   the user might already exist on Clerk under a different id; the
   resolver handles whichever id Clerk hands out.

Usage::

    python3 seed_first_admin.py \\
        --email me@example.com \\
        --role admin \\
        --full-name "Jane Admin"

Re-runs are safe — the script reports "already exists" for both sides
and exits 0.

The script reads ``CLERK_SECRET_KEY`` from the environment. If it's
missing the Clerk step is skipped (and a warning is printed) so the
local row can still be seeded in environments that haven't set up
Clerk yet.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

import httpx
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.admin import Admin

CLERK_API_BASE = os.environ.get("CLERK_API_BASE", "https://api.clerk.com/v1")
CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY", "")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("seed_first_admin")


def _local_username(email: str) -> str:
    base = email.split("@", 1)[0][:50] or "admin"
    return "".join(c for c in base if c.isalnum() or c in "._-") or "admin"


async def ensure_local_admin(email: str, role: str, full_name: Optional[str]) -> Admin:
    """Insert-or-update the local admins row. Returns the row."""
    async with AsyncSessionLocal() as db:
        row = (
            await db.execute(select(Admin).where(Admin.email == email))
        ).scalar_one_or_none()

        if row is not None:
            changed = False
            if row.role != role:
                row.role = role
                changed = True
            if not row.is_active:
                row.is_active = True
                changed = True
            if (role == "admin") != bool(row.is_superuser):
                row.is_superuser = (role == "admin")
                changed = True
            if full_name and row.full_name != full_name:
                row.full_name = full_name
                changed = True
            if changed:
                await db.commit()
                log.info("local admin row updated (id=%s)", row.id)
            else:
                log.info("local admin row already correct (id=%s)", row.id)
            return row

        row = Admin(
            email=email,
            username=_local_username(email),
            hashed_password=None,
            full_name=full_name,
            is_active=True,
            is_superuser=(role == "admin"),
            role=role,
        )
        db.add(row)
        await db.commit()
        await db.refresh(row)
        log.info("local admin row created (id=%s, email=%s, role=%s)",
                 row.id, row.email, row.role)
        return row


async def _clerk_request(method: str, path: str, *, json=None, params=None) -> dict:
    url = f"{CLERK_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {CLERK_SECRET_KEY}",
               "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.request(method, url, headers=headers, json=json, params=params)
    if resp.status_code >= 400:
        body = resp.text
        try:
            body = resp.json()
        except Exception:
            pass
        raise RuntimeError(f"Clerk {method} {path} → {resp.status_code}: {body}")
    return resp.json() if resp.content else {}


async def ensure_clerk_user(email: str, full_name: Optional[str]) -> Optional[str]:
    """Find or create the Clerk user for ``email``. Returns the Clerk user id."""
    if not CLERK_SECRET_KEY:
        log.warning("CLERK_SECRET_KEY not set — skipping Clerk user creation. "
                    "On first sign-in the user must already exist in Clerk.")
        return None

    existing = await _clerk_request("GET", "users", params={"email_address": email})
    if isinstance(existing, list) and existing:
        user_id = existing[0].get("id")
        log.info("Clerk user already exists (id=%s)", user_id)
        return user_id

    first, _, last = (full_name or "").partition(" ")
    payload = {
        "email_address": [email],
        "skip_password_requirement": True,
        "skip_password_checks": True,
    }
    if first:
        payload["first_name"] = first
    if last:
        payload["last_name"] = last

    created = await _clerk_request("POST", "users", json=payload)
    user_id = created.get("id")
    log.info("Clerk user created (id=%s). Email is verified; user can sign in "
             "with any enabled method (Google / magic link / password reset).",
             user_id)
    return user_id


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Idempotently seed the first administrator (local DB + Clerk).",
    )
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--role", default="admin",
                        choices=["admin", "editor", "viewer"],
                        help="Local role (default: admin)")
    parser.add_argument("--full-name", default=None,
                        help="Optional display name, e.g. 'Jane Admin'")
    args = parser.parse_args()

    email = args.email.strip().lower()
    role = args.role
    full_name = (args.full_name or "").strip() or None

    try:
        row = await ensure_local_admin(email, role, full_name)
    except Exception as e:  # noqa: BLE001
        log.error("Local admin seeding failed: %s", e)
        return 2

    try:
        await ensure_clerk_user(email, full_name)
    except Exception as e:  # noqa: BLE001
        log.error("Clerk user seeding failed: %s", e)
        log.error("Local admin row was created/updated, but Clerk side did "
                  "not finish. Re-run after fixing the Clerk credentials, "
                  "or create the user manually in Clerk's dashboard.")
        return 3

    print()
    print("=" * 60)
    print("Bootstrap complete.")
    print(f"  Local admin: id={row.id} email={row.email} role={row.role}")
    print(f"  Next step  : sign in at the app's /login with this email.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
