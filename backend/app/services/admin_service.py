"""
Admin user service for CRUD operations
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.schemas.admin import AdminCreate, AdminInvite, AdminUpdate


class AdminService:
    """
    Service for admin user operations
    """

    @staticmethod
    async def get_by_id(db: AsyncSession, admin_id: int) -> Optional[Admin]:
        """
        Get admin by ID

        Args:
            db: Database session
            admin_id: Admin ID

        Returns:
            Admin or None
        """
        result = await db.execute(
            select(Admin).where(Admin.id == admin_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[Admin]:
        """
        Get admin by email

        Args:
            db: Database session
            email: Admin email

        Returns:
            Admin or None
        """
        result = await db.execute(
            select(Admin).where(Admin.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[Admin]:
        """
        Get admin by username

        Args:
            db: Database session
            username: Admin username

        Returns:
            Admin or None
        """
        result = await db.execute(
            select(Admin).where(Admin.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_clerk_user_id(
        db: AsyncSession, clerk_user_id: str
    ) -> Optional[Admin]:
        """Look up an admin by its linked Clerk user ID."""
        result = await db.execute(
            select(Admin).where(Admin.clerk_user_id == clerk_user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def link_clerk_user(
        db: AsyncSession, admin_id: int, clerk_user_id: str
    ) -> Optional[Admin]:
        """Write ``clerk_user_id`` onto an existing admin row."""
        admin = await AdminService.get_by_id(db, admin_id)
        if admin is None:
            return None
        admin.clerk_user_id = clerk_user_id
        await db.flush()
        await db.refresh(admin)
        return admin

    @staticmethod
    async def create_invited(db: AsyncSession, data: AdminInvite) -> Admin:
        """
        Create a pending admin row for an invited user.

        The row carries ``is_active=False`` and a placeholder username
        derived from the email until the user finishes Clerk sign-in,
        at which point ``link_clerk_user`` writes ``clerk_user_id`` and
        ``is_active`` flips to True.
        """
        existing = await AdminService.get_by_email(db, data.email)
        if existing:
            raise ValueError(f"Email {data.email} is already invited or registered")

        username_base = data.email.split("@", 1)[0][:50] or "user"
        username = username_base
        suffix = 1
        while await AdminService.get_by_username(db, username):
            suffix += 1
            username = f"{username_base[:46]}-{suffix}"

        admin = Admin(
            email=data.email,
            username=username,
            hashed_password=None,
            full_name=data.full_name,
            is_active=False,
            is_superuser=(data.role == "admin"),
            role=data.role,
        )
        db.add(admin)
        await db.flush()
        await db.refresh(admin)
        return admin

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Admin]:
        """
        Get all admins with pagination

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of admins
        """
        result = await db.execute(
            select(Admin)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, admin_data: AdminCreate) -> Admin:
        """
        Create a new admin

        Args:
            db: Database session
            admin_data: Admin creation data

        Returns:
            Created admin

        Raises:
            ValueError: If email or username already exists
        """
        # Check if email already exists
        existing = await AdminService.get_by_email(db, admin_data.email)
        if existing:
            raise ValueError(f"Email {admin_data.email} is already registered")

        # Check if username already exists
        existing = await AdminService.get_by_username(db, admin_data.username)
        if existing:
            raise ValueError(f"Username {admin_data.username} is already taken")

        admin = Admin(
            email=admin_data.email,
            username=admin_data.username,
            hashed_password=None,  # authentication is delegated to Clerk
            full_name=admin_data.full_name,
            is_active=admin_data.is_active,
            is_superuser=admin_data.is_superuser,
            role=admin_data.role,
        )

        db.add(admin)
        await db.flush()
        await db.refresh(admin)

        return admin

    @staticmethod
    async def update(
        db: AsyncSession,
        admin_id: int,
        admin_data: AdminUpdate
    ) -> Optional[Admin]:
        """
        Update an admin

        Args:
            db: Database session
            admin_id: Admin ID
            admin_data: Update data

        Returns:
            Updated admin or None if not found

        Raises:
            ValueError: If email or username already exists for another admin
        """
        admin = await AdminService.get_by_id(db, admin_id)
        if not admin:
            return None

        # Check email uniqueness if being updated
        if admin_data.email is not None and admin_data.email != admin.email:
            existing = await AdminService.get_by_email(db, admin_data.email)
            if existing and existing.id != admin_id:
                raise ValueError(f"Email {admin_data.email} is already registered")
            admin.email = admin_data.email

        # Check username uniqueness if being updated
        if admin_data.username is not None and admin_data.username != admin.username:
            existing = await AdminService.get_by_username(db, admin_data.username)
            if existing and existing.id != admin_id:
                raise ValueError(f"Username {admin_data.username} is already taken")
            admin.username = admin_data.username

        # Update other fields
        if admin_data.full_name is not None:
            admin.full_name = admin_data.full_name
        if admin_data.is_active is not None:
            admin.is_active = admin_data.is_active
        if admin_data.is_superuser is not None:
            admin.is_superuser = admin_data.is_superuser
        if admin_data.role is not None:
            admin.role = admin_data.role
        # ``modules`` distinguishes three intents via ``model_fields_set``:
        #   * field absent          → leave unchanged
        #   * present as null       → reset to role defaults (store NULL)
        #   * present as a list      → explicit allow-list (``[]`` = no modules)
        if "modules" in admin_data.model_fields_set:
            admin.modules = admin_data.modules

        await db.flush()
        await db.refresh(admin)

        return admin

    @staticmethod
    async def delete(db: AsyncSession, admin_id: int) -> bool:
        """
        Delete an admin

        Args:
            db: Database session
            admin_id: Admin ID

        Returns:
            True if deleted, False if not found
        """
        admin = await AdminService.get_by_id(db, admin_id)
        if not admin:
            return False

        await db.delete(admin)
        await db.flush()

        return True
