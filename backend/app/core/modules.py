"""
Module registry and per-user module access control.

A *module* corresponds to one function in the sidebar (Members, Events,
Expenses, …). Access is a second, orthogonal axis to ``role``:

    role    → *how much* a user can do inside a module (view vs edit)
    modules → *which* modules a user can reach at all

Each ``Admin`` row carries an optional ``modules`` JSON list:

    * ``None``  → not customised; fall back to the role's default set
                  (this keeps every pre-existing user working unchanged).
    * ``[...]`` → an explicit allow-list chosen by an admin.

Admins / superusers always get every module regardless of the stored
value, so they can never lock themselves out of Settings.
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Registry — the single source of truth for what modules exist.
# Keep the ``key`` values in sync with the frontend sidebar nav items.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ModuleDef:
    key: str          # stable identifier, used in the DB and API guards
    label: str        # human label for the admin editor UI
    group: str        # sidebar group it belongs to (display grouping only)


MODULES: tuple[ModuleDef, ...] = (
    ModuleDef("dashboard", "Dashboard", "Core"),
    ModuleDef("members", "Members", "People"),
    ModuleDef("events", "Events & Training", "Activities"),
    ModuleDef("training", "Training plan", "Activities"),
    ModuleDef("competitions", "Konkurranser", "Activities"),
    ModuleDef("scores", "Scores & Records", "Performance"),
    ModuleDef("expenses", "Utlegg", "Operations"),
    ModuleDef("projects", "Prosjekter", "Operations"),
    ModuleDef("forms", "Skjema", "Operations"),
    ModuleDef("reports", "Reports", "Intelligence"),
    ModuleDef("analytics", "Analytics", "Intelligence"),
    ModuleDef("settings", "Settings", "System"),
)

ALL_MODULE_KEYS: frozenset[str] = frozenset(m.key for m in MODULES)


# ---------------------------------------------------------------------------
# Seed defaults: role → default module set.
#
# These values only *seed* the editable ``role_module_defaults`` table on first
# migration, and act as a fallback if a role's DB row is ever missing. Once
# seeded, admins edit the live defaults in Settings › Roles & Access, not here.
#
#   * viewer   — read-only club members: the everyday, non-sensitive views.
#   * editor   — content managers: everything a viewer sees, plus the
#                modules they actively maintain.
#   * kasserer — treasurer: focused on the expense queue (+ basic context).
#   * admin    — not listed; admins always get ALL modules.
# ---------------------------------------------------------------------------
SEED_ROLE_DEFAULT_MODULES: dict[str, frozenset[str]] = {
    "admin": ALL_MODULE_KEYS,
    "viewer": frozenset({
        "dashboard", "members", "events", "competitions",
        "scores", "projects", "reports",
    }),
    "editor": frozenset({
        "dashboard", "members", "events", "training", "competitions",
        "scores", "expenses", "projects", "forms", "reports", "analytics",
    }),
    "kasserer": frozenset({
        "dashboard", "expenses", "members",
    }),
}


def resolve_modules(admin, role_defaults: dict[str, list[str]]) -> frozenset[str]:
    """
    Pure resolution of the module set ``admin`` may access, given the current
    role-default map (loaded from the DB by the caller).

    Precedence (most specific wins):
      1. Admins / superusers → every module (never lock them out).
      2. Explicit per-user ``modules`` list → that set (an override).
      3. Assigned access group → the group's module set.
      4. Otherwise → the role's default set.

    Every branch is filtered to the registry so a stale/removed key can't
    grant phantom access.
    """
    from app.models.admin import UserRole

    if getattr(admin, "is_superuser", False) or admin.role == UserRole.ADMIN.value:
        return ALL_MODULE_KEYS

    stored = getattr(admin, "modules", None)
    if stored is not None:
        return frozenset(stored) & ALL_MODULE_KEYS

    group = getattr(admin, "access_group", None)
    if group is not None:
        return frozenset(group.modules or ()) & ALL_MODULE_KEYS

    return frozenset(role_defaults.get(admin.role, ())) & ALL_MODULE_KEYS


def require_module(module_key: str):
    """
    Dependency factory: 403 unless the current user can reach ``module_key``.

    Applied at ``include_router`` time in ``main.py`` so every endpoint
    under a router inherits the guard without per-handler wiring.
    """
    from fastapi import Depends, HTTPException, status
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.deps import get_current_user
    from app.db.session import get_db
    from app.models.admin import Admin
    from app.services.access_service import AccessService

    async def module_checker(
        current_user: "Admin" = Depends(get_current_user),
        db: "AsyncSession" = Depends(get_db),
    ) -> "Admin":
        modules = await AccessService.resolve_effective_modules(db, current_user)
        if module_key not in modules:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have access to the '{module_key}' module.",
            )
        return current_user

    return module_checker
