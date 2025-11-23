"""
Script to create an admin user for testing
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal, init_db
from app.models.admin import Admin
from app.core.security import get_password_hash


async def create_admin_user():
    """Create an admin user if it doesn't exist"""
    print("Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # Check if admin user already exists
        result = await db.execute(
            select(Admin).where(Admin.username == "admin")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            # Update the password if user exists
            print(f"Admin user already exists (ID: {existing_admin.id})")
            print("Updating password to 'TestPass123!'...")
            existing_admin.hashed_password = get_password_hash("TestPass123!")
            await db.commit()
            print("✅ Password updated successfully!")
        else:
            # Create new admin user
            print("Creating new admin user...")
            admin = Admin(
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("TestPass123!"),
                full_name="Admin User",
                is_active=True,
                is_superuser=True
            )
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            print(f"✅ Admin user created successfully (ID: {admin.id})")

        print("\nAdmin credentials:")
        print("  Username: admin")
        print("  Password: TestPass123!")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
