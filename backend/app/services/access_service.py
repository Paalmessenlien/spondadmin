"""
Access-control service: effective-module resolution, access groups, and
editable role defaults.

Resolution precedence (see ``app.core.modules.resolve_modules``):
    admin/superuser → all
    explicit per-user modules → those
    assigned access group → group's modules
    role default (from ``role_module_defaults``) → fallback
"""
from typing import Optional, List, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.modules import (
    ALL_MODULE_KEYS,
    SEED_ROLE_DEFAULT_MODULES,
)
from app.models.access_group import AccessGroup, RoleModuleDefault
from app.models.admin import Admin, UserRole

# Roles whose default module set is editable in the UI. ``admin`` is omitted:
# admins always get every module and their defaults aren't user-editable.
EDITABLE_DEFAULT_ROLES = ("editor", "viewer", "kasserer")


def _clean_modules(keys: Sequence[str]) -> List[str]:
    """Drop unknown keys and de-dupe, preserving a stable sorted order."""
    return sorted({k for k in (keys or []) if k in ALL_MODULE_KEYS})


class AccessService:
    # ---- role defaults --------------------------------------------------
    @staticmethod
    async def get_role_defaults(db: AsyncSession) -> dict[str, list[str]]:
        """
        Load the role → default-modules map from the DB, falling back to the
        seed constant for any role missing a row (keeps resolution robust even
        before the seeding migration has populated every role).
        """
        result = await db.execute(select(RoleModuleDefault))
        stored = {r.role: list(r.modules or []) for r in result.scalars().all()}
        merged: dict[str, list[str]] = {
            role: sorted(mods) for role, mods in SEED_ROLE_DEFAULT_MODULES.items()
        }
        merged.update(stored)
        return merged

    @staticmethod
    async def set_role_default(
        db: AsyncSession, role: str, modules: Sequence[str]
    ) -> RoleModuleDefault:
        """Upsert one role's default module set (admins aren't editable)."""
        if role not in EDITABLE_DEFAULT_ROLES:
            raise ValueError(f"Role '{role}' defaults are not editable.")
        cleaned = _clean_modules(modules)
        row = await db.get(RoleModuleDefault, role)
        if row is None:
            row = RoleModuleDefault(role=role, modules=cleaned)
            db.add(row)
        else:
            row.modules = cleaned
        await db.flush()
        await db.refresh(row)
        return row

    # ---- resolution -----------------------------------------------------
    @staticmethod
    async def resolve_effective_modules(db: AsyncSession, admin: Admin) -> frozenset[str]:
        """
        The set of modules ``admin`` may actually reach. Short-circuits the
        common cases so only pure role-default users incur the defaults query.
        """
        if getattr(admin, "is_superuser", False) or admin.role == UserRole.ADMIN.value:
            return ALL_MODULE_KEYS
        if admin.modules is not None:
            return frozenset(admin.modules) & ALL_MODULE_KEYS
        if admin.access_group is not None:
            return frozenset(admin.access_group.modules or ()) & ALL_MODULE_KEYS
        defaults = await AccessService.get_role_defaults(db)
        return frozenset(defaults.get(admin.role, ())) & ALL_MODULE_KEYS

    # ---- access groups --------------------------------------------------
    @staticmethod
    async def list_groups(db: AsyncSession) -> List[AccessGroup]:
        result = await db.execute(select(AccessGroup).order_by(AccessGroup.name))
        return list(result.scalars().all())

    @staticmethod
    async def get_group(db: AsyncSession, group_id: int) -> Optional[AccessGroup]:
        return await db.get(AccessGroup, group_id)

    @staticmethod
    async def get_group_by_name(db: AsyncSession, name: str) -> Optional[AccessGroup]:
        result = await db.execute(select(AccessGroup).where(AccessGroup.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_group(
        db: AsyncSession, name: str, description: Optional[str], role: str, modules: Sequence[str]
    ) -> AccessGroup:
        if await AccessService.get_group_by_name(db, name):
            raise ValueError(f"An access group named '{name}' already exists.")
        if role not in {r.value for r in UserRole}:
            raise ValueError(f"Unknown role '{role}'.")
        group = AccessGroup(
            name=name,
            description=description,
            role=role,
            modules=_clean_modules(modules),
        )
        db.add(group)
        await db.flush()
        await db.refresh(group)
        return group

    @staticmethod
    async def update_group(
        db: AsyncSession,
        group_id: int,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        role: Optional[str] = None,
        modules: Optional[Sequence[str]] = None,
    ) -> Optional[AccessGroup]:
        group = await db.get(AccessGroup, group_id)
        if group is None:
            return None
        if name is not None and name != group.name:
            if await AccessService.get_group_by_name(db, name):
                raise ValueError(f"An access group named '{name}' already exists.")
            group.name = name
        if description is not None:
            group.description = description
        if modules is not None:
            group.modules = _clean_modules(modules)
        if role is not None and role != group.role:
            if role not in {r.value for r in UserRole}:
                raise ValueError(f"Unknown role '{role}'.")
            group.role = role
            # Live-linked: propagate the new role to every member so all
            # existing role guards (which read admins.role) stay correct.
            await db.execute(
                update(Admin)
                .where(Admin.access_group_id == group_id)
                .values(role=role, is_superuser=(role == UserRole.ADMIN.value))
            )
        await db.flush()
        await db.refresh(group)
        return group

    @staticmethod
    async def delete_group(db: AsyncSession, group_id: int) -> bool:
        group = await db.get(AccessGroup, group_id)
        if group is None:
            return False
        # ondelete=SET NULL detaches members; they fall back to role defaults.
        await db.delete(group)
        await db.flush()
        return True

    @staticmethod
    async def count_members(db: AsyncSession, group_id: int) -> int:
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(Admin.id)).where(Admin.access_group_id == group_id)
        )
        return int(result.scalar_one())

    # ---- assignment -----------------------------------------------------
    @staticmethod
    async def assign_group(db: AsyncSession, admin: Admin, group_id: Optional[int]) -> Admin:
        """
        Put ``admin`` in a group (or detach when ``group_id`` is None).

        Assigning copies the group's role onto the user and clears any
        per-user module override so they inherit the group's modules live.
        """
        if group_id is None:
            admin.access_group_id = None
            return admin
        group = await db.get(AccessGroup, group_id)
        if group is None:
            raise ValueError("Access group not found.")
        admin.access_group_id = group.id
        admin.role = group.role
        admin.is_superuser = group.role == UserRole.ADMIN.value
        admin.modules = None  # inherit the group's modules
        return admin
