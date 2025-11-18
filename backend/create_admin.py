#!/usr/bin/env python3
"""
Script to create an initial admin user

Usage:
    python create_admin.py
"""
import asyncio
import sys
from getpass import getpass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.schemas.admin import AdminCreate
from app.services.admin_service import AdminService


async def create_admin():
    """
    Create an admin user interactively
    """
    print("=" * 50)
    print("Create Admin User")
    print("=" * 50)
    print()

    # Get admin details
    username = input("Username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        return

    email = input("Email: ").strip()
    if not email:
        print("Error: Email cannot be empty")
        return

    full_name = input("Full Name (optional): ").strip() or None

    password = getpass("Password: ")
    if len(password) < 8:
        print("Error: Password must be at least 8 characters")
        return

    password_confirm = getpass("Confirm Password: ")
    if password != password_confirm:
        print("Error: Passwords do not match")
        return

    is_superuser_input = input("Is superuser? (y/N): ").strip().lower()
    is_superuser = is_superuser_input in ['y', 'yes']

    print()
    print("Creating admin user...")

    # Create admin
    async with AsyncSessionLocal() as db:
        try:
            admin_data = AdminCreate(
                username=username,
                email=email,
                full_name=full_name,
                password=password,
                is_active=True,
                is_superuser=is_superuser,
            )

            admin = await AdminService.create(db, admin_data)
            await db.commit()

            print()
            print("✓ Admin user created successfully!")
            print()
            print(f"  Username: {admin.username}")
            print(f"  Email: {admin.email}")
            print(f"  Full Name: {admin.full_name or 'N/A'}")
            print(f"  Superuser: {'Yes' if admin.is_superuser else 'No'}")
            print(f"  Active: {'Yes' if admin.is_active else 'No'}")
            print()

        except ValueError as e:
            print(f"\nError: {e}")
            await db.rollback()
            sys.exit(1)
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            await db.rollback()
            sys.exit(1)


async def list_admins():
    """
    List all existing admins
    """
    print("=" * 50)
    print("Existing Admin Users")
    print("=" * 50)
    print()

    async with AsyncSessionLocal() as db:
        admins = await AdminService.get_all(db)

        if not admins:
            print("No admin users found.")
            print()
            return

        for admin in admins:
            print(f"  • {admin.username} ({admin.email})")
            print(f"    Full Name: {admin.full_name or 'N/A'}")
            print(f"    Superuser: {'Yes' if admin.is_superuser else 'No'}")
            print(f"    Active: {'Yes' if admin.is_active else 'No'}")
            print()


async def main():
    """
    Main function
    """
    # Show existing admins
    await list_admins()

    # Ask if user wants to create a new admin
    create = input("Do you want to create a new admin user? (Y/n): ").strip().lower()

    if create in ['', 'y', 'yes']:
        await create_admin()
    else:
        print("Cancelled.")


if __name__ == "__main__":
    asyncio.run(main())
