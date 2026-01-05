#!/usr/bin/env python3
"""
Script to change the admin password
Usage: python change_admin_password.py
"""
import asyncio
import sys
from getpass import getpass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.services.admin_service import AdminService
from app.schemas.admin import AdminUpdate


async def change_password():
    """Change admin password"""

    # Get username
    username = input("Enter admin username (default: testadmin): ").strip() or "testadmin"

    # Get new password
    while True:
        new_password = getpass("Enter new password (minimum 8 characters): ")
        if len(new_password) < 8:
            print("❌ Password must be at least 8 characters long")
            continue

        confirm_password = getpass("Confirm new password: ")
        if new_password != confirm_password:
            print("❌ Passwords do not match. Please try again.")
            continue

        break

    # Update password in database
    async with async_session_maker() as db:
        try:
            # Get admin by username
            admin = await AdminService.get_by_username(db, username)
            if not admin:
                print(f"❌ Admin user '{username}' not found")
                return

            # Update password
            admin_data = AdminUpdate(password=new_password)
            updated_admin = await AdminService.update(db, admin.id, admin_data)

            if updated_admin:
                await db.commit()
                print(f"✅ Password updated successfully for user '{username}'")
            else:
                print(f"❌ Failed to update password for user '{username}'")

        except Exception as e:
            await db.rollback()
            print(f"❌ Error updating password: {e}")
            sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("Admin Password Change Tool")
    print("=" * 50)
    print()

    asyncio.run(change_password())
