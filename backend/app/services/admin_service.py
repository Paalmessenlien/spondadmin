"""
Admin user service for CRUD operations
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.schemas.admin import AdminCreate, AdminUpdate
from app.core.security import get_password_hash, verify_password


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

        # Hash password
        hashed_password = get_password_hash(admin_data.password)

        # Create admin
        admin = Admin(
            email=admin_data.email,
            username=admin_data.username,
            hashed_password=hashed_password,
            full_name=admin_data.full_name,
            is_active=admin_data.is_active,
            is_superuser=admin_data.is_superuser,
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

        # Update password if provided
        if admin_data.password is not None:
            admin.hashed_password = get_password_hash(admin_data.password)

        # Update other fields
        if admin_data.full_name is not None:
            admin.full_name = admin_data.full_name
        if admin_data.is_active is not None:
            admin.is_active = admin_data.is_active
        if admin_data.is_superuser is not None:
            admin.is_superuser = admin_data.is_superuser

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

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[Admin]:
        """
        Authenticate an admin by username and password

        Args:
            db: Database session
            username: Admin username
            password: Plain text password

        Returns:
            Admin if authenticated, None otherwise
        """
        admin = await AdminService.get_by_username(db, username)
        if not admin:
            return None

        if not verify_password(password, admin.hashed_password):
            return None

        if not admin.is_active:
            return None

        return admin
