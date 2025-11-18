"""
Script to reset admin password for testing
"""
import asyncio
from app.db.session import AsyncSessionLocal
from app.services.admin_service import AdminService
from app.schemas.admin import AdminUpdate

async def reset_password():
    async with AsyncSessionLocal() as db:
        try:
            # Get admin
            admin = await AdminService.get_by_username(db, "testadmin")
            if not admin:
                print("✗ Admin 'testadmin' not found")
                return

            # Update password
            update_data = AdminUpdate(password="TestPass123!")
            updated = await AdminService.update(db, admin.id, update_data)
            await db.commit()

            print(f"✓ Password reset for 'testadmin' (ID: {admin.id})")
            print(f"  Username: testadmin")
            print(f"  New Password: TestPass123!")

        except Exception as e:
            await db.rollback()
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(reset_password())
