"""
Script to create a test admin user for testing
"""
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.admin_service import AdminService
from app.schemas.admin import AdminCreate

async def create_admin():
    async with AsyncSessionLocal() as db:
        try:
            # Check if admin exists
            existing = await AdminService.get_by_username(db, "testadmin")
            if existing:
                print(f"Admin 'testadmin' already exists (ID: {existing.id})")
                return

            # Create admin with strong password
            admin_data = AdminCreate(
                username="testadmin",
                email="testadmin@example.com",
                password="TestPass123!",  # Strong password
                is_superuser=True
            )

            admin = await AdminService.create(db, admin_data)
            await db.commit()
            print(f"✓ Created admin 'testadmin' (ID: {admin.id})")
            print(f"  Username: testadmin")
            print(f"  Password: TestPass123!")
            print(f"  Email: testadmin@example.com")

        except Exception as e:
            await db.rollback()
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_admin())
