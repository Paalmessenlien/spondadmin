"""
Migration management service - wraps Alembic operations
"""
import logging
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

ALEMBIC_DIR = Path(__file__).resolve().parent.parent.parent / "alembic"
VERSIONS_DIR = ALEMBIC_DIR / "versions"


class MigrationService:

    @staticmethod
    async def get_migration_status(db: AsyncSession) -> dict:
        """Get current migration status."""
        current_rev = await MigrationService._get_current_revision(db)
        migrations = MigrationService._discover_migrations()

        # Find head revision
        head_rev = migrations[-1]["revision"] if migrations else None

        # Count applied vs pending
        applied = []
        pending = []
        found_current = current_rev is None

        for m in migrations:
            if found_current:
                pending.append(m)
            elif m["revision"] == current_rev:
                applied.append(m)
                found_current = True
            else:
                applied.append(m)

        is_up_to_date = current_rev == head_rev if head_rev else True

        return {
            "current_revision": current_rev,
            "head_revision": head_rev,
            "is_up_to_date": is_up_to_date,
            "applied_count": len(applied),
            "pending_count": len(pending),
            "pending_migrations": pending,
        }

    @staticmethod
    async def get_migration_history(db: AsyncSession) -> list[dict]:
        """List all discovered migrations with applied status."""
        current_rev = await MigrationService._get_current_revision(db)
        migrations = MigrationService._discover_migrations()

        found_current = current_rev is None
        for m in migrations:
            if found_current:
                m["applied"] = False
            elif m["revision"] == current_rev:
                m["applied"] = True
                found_current = True
            else:
                m["applied"] = True

        return migrations

    @staticmethod
    async def run_migrations(db: AsyncSession) -> dict:
        """Run pending migrations via alembic upgrade head."""
        import subprocess

        # Get pre-migration status
        status_before = await MigrationService.get_migration_status(db)

        if status_before["is_up_to_date"]:
            return {
                "status": "already_up_to_date",
                "current_revision": status_before["current_revision"],
                "migrations_applied": 0,
            }

        # Run alembic upgrade head
        backend_dir = ALEMBIC_DIR.parent
        env = os.environ.copy()

        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(backend_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            logger.error(f"Migration failed: {result.stderr}")
            raise RuntimeError(f"Migration failed: {result.stderr}")

        # Get post-migration status
        status_after = await MigrationService.get_migration_status(db)

        return {
            "status": "completed",
            "previous_revision": status_before["current_revision"],
            "current_revision": status_after["current_revision"],
            "migrations_applied": status_before["pending_count"],
            "output": result.stdout,
        }

    @staticmethod
    async def _get_current_revision(db: AsyncSession) -> Optional[str]:
        """Read current revision from alembic_version table."""
        try:
            result = await db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            row = result.scalar()
            return row
        except Exception:
            return None

    @staticmethod
    def _discover_migrations() -> list[dict]:
        """Scan alembic/versions/ directory for migration files."""
        migrations = []

        if not VERSIONS_DIR.exists():
            return migrations

        for f in sorted(VERSIONS_DIR.glob("*.py")):
            if f.name == "__pycache__" or f.name.startswith("__"):
                continue

            name = f.stem
            # Extract revision from filename (typically revision_description.py)
            parts = name.split("_", 1)
            revision = parts[0] if parts else name
            description = parts[1].replace("_", " ") if len(parts) > 1 else name

            migrations.append({
                "revision": revision,
                "description": description,
                "filename": f.name,
            })

        return migrations
