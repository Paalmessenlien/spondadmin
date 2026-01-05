#!/usr/bin/env python3
"""
Script to reset admin password with a secure random password
Usage: python reset_admin_password.py
"""
import asyncio
import secrets
import string
import sys

from app.db.session import AsyncSessionLocal
from app.services.admin_service import AdminService
from app.schemas.admin import AdminUpdate


def generate_secure_password(length: int = 16) -> str:
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


async def reset_password():
    """Reset admin password to a new secure random password"""

    username = "testadmin"

    # Generate a secure random password
    new_password = generate_secure_password(16)

    # Update password in database
    async with AsyncSessionLocal() as db:
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
                print("=" * 60)
                print("✅ Password updated successfully!")
                print("=" * 60)
                print(f"Username: {username}")
                print(f"New Password: {new_password}")
                print("=" * 60)
                print()
                print("⚠️  IMPORTANT: Save this password securely!")
                print("   This password will not be shown again.")
                print("=" * 60)
            else:
                print(f"❌ Failed to update password for user '{username}'")

        except Exception as e:
            await db.rollback()
            print(f"❌ Error updating password: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(reset_password())
