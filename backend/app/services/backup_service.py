"""
Backup service - pg_dump + Bunny CDN upload
"""
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database_backup import DatabaseBackup

logger = logging.getLogger(__name__)

BACKUP_DIR = Path("/app/backups")


class BackupService:

    @staticmethod
    async def create_backup(
        db: AsyncSession,
        backup_type: str = "manual",
        created_by: Optional[int] = None,
    ) -> DatabaseBackup:
        """Create a PostgreSQL backup using pg_dump."""
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"spondadmin_{backup_type}_{timestamp}.dump"
        file_path = BACKUP_DIR / filename

        # Create DB record
        backup = DatabaseBackup(
            filename=filename,
            file_path=str(file_path),
            backup_type=backup_type,
            status="in_progress",
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(backup)
        await db.commit()
        await db.refresh(backup)

        try:
            # Parse DATABASE_URL for pg_dump
            db_url = settings.DATABASE_URL
            # Convert async URL to sync for pg_dump
            if db_url.startswith("postgresql+asyncpg://"):
                db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

            parsed = urlparse(db_url)
            env = os.environ.copy()
            env["PGPASSWORD"] = parsed.password or ""

            cmd = [
                "pg_dump",
                "-h", parsed.hostname or "db",
                "-p", str(parsed.port or 5432),
                "-U", parsed.username or "postgres",
                "-d", parsed.path.lstrip("/"),
                "-Fc",  # custom format with compression
                "-f", str(file_path),
            ]

            result = subprocess.run(
                cmd, env=env, capture_output=True, text=True, timeout=300
            )

            if result.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {result.stderr}")

            # Update record with file size and metadata
            size_bytes = file_path.stat().st_size
            metadata = await BackupService._collect_database_metadata(db)

            backup.status = "completed"
            backup.size_bytes = size_bytes
            backup.backup_metadata = metadata
            backup.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(backup)

            logger.info(f"Backup created: {filename} ({size_bytes} bytes)")
            return backup

        except Exception as e:
            backup.status = "failed"
            backup.backup_metadata = {"error": str(e)}
            backup.updated_at = datetime.utcnow()
            await db.commit()
            logger.error(f"Backup failed: {e}")
            raise

    @staticmethod
    async def upload_to_cdn(db: AsyncSession, backup_id: int) -> DatabaseBackup:
        """Upload a backup file to Bunny CDN."""
        backup = await db.get(DatabaseBackup, backup_id)
        if not backup:
            raise ValueError("Backup not found")

        if not backup.file_path or not Path(backup.file_path).exists():
            raise ValueError("Backup file not found on disk")

        if not settings.BUNNY_STORAGE_API_KEY:
            raise ValueError("Bunny CDN not configured")

        cdn_path = f"spondadmin/backups/{backup.filename}"
        storage_zone = settings.BUNNY_STORAGE_ZONE

        # Determine storage endpoint
        region = settings.BUNNY_STORAGE_REGION
        if region:
            base_url = f"https://{region}.storage.bunnycdn.com"
        else:
            base_url = "https://storage.bunnycdn.com"

        upload_url = f"{base_url}/{storage_zone}/{cdn_path}"

        try:
            with open(backup.file_path, "rb") as f:
                file_data = f.read()

            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.put(
                    upload_url,
                    content=file_data,
                    headers={
                        "AccessKey": settings.BUNNY_STORAGE_API_KEY,
                        "Content-Type": "application/octet-stream",
                    },
                )
                response.raise_for_status()

            cdn_hostname = settings.BUNNY_CDN_HOSTNAME
            backup.cdn_url = f"https://{cdn_hostname}/{cdn_path}"
            backup.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(backup)

            logger.info(f"Backup uploaded to CDN: {backup.cdn_url}")
            return backup

        except Exception as e:
            logger.error(f"CDN upload failed: {e}")
            raise

    @staticmethod
    async def list_backups(db: AsyncSession) -> list[DatabaseBackup]:
        """List all backups ordered by creation date."""
        result = await db.execute(
            select(DatabaseBackup).order_by(DatabaseBackup.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_backup(db: AsyncSession, backup_id: int) -> Optional[DatabaseBackup]:
        """Get a single backup by ID."""
        return await db.get(DatabaseBackup, backup_id)

    @staticmethod
    async def delete_backup(db: AsyncSession, backup_id: int) -> None:
        """Delete backup: local file + CDN + DB record."""
        backup = await db.get(DatabaseBackup, backup_id)
        if not backup:
            raise ValueError("Backup not found")

        # Delete local file
        if backup.file_path and Path(backup.file_path).exists():
            Path(backup.file_path).unlink()

        # Delete from CDN if uploaded
        if backup.cdn_url and settings.BUNNY_STORAGE_API_KEY:
            try:
                cdn_path = f"spondadmin/backups/{backup.filename}"
                storage_zone = settings.BUNNY_STORAGE_ZONE
                region = settings.BUNNY_STORAGE_REGION
                if region:
                    base_url = f"https://{region}.storage.bunnycdn.com"
                else:
                    base_url = "https://storage.bunnycdn.com"

                delete_url = f"{base_url}/{storage_zone}/{cdn_path}"

                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.delete(
                        delete_url,
                        headers={"AccessKey": settings.BUNNY_STORAGE_API_KEY},
                    )
                    response.raise_for_status()
            except Exception as e:
                logger.warning(f"Failed to delete from CDN: {e}")

        # Delete DB record
        await db.delete(backup)
        await db.commit()
        logger.info(f"Backup deleted: {backup.filename}")

    @staticmethod
    async def restore_from_backup(db: AsyncSession, backup_id: int) -> dict:
        """Restore database from a backup file."""
        backup = await db.get(DatabaseBackup, backup_id)
        if not backup:
            raise ValueError("Backup not found")

        file_path = backup.file_path
        if not file_path or not Path(file_path).exists():
            # Try downloading from CDN
            if backup.cdn_url and settings.BUNNY_STORAGE_API_KEY:
                BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                file_path = str(BACKUP_DIR / backup.filename)
                cdn_path = f"spondadmin/backups/{backup.filename}"
                storage_zone = settings.BUNNY_STORAGE_ZONE
                region = settings.BUNNY_STORAGE_REGION
                if region:
                    base_url = f"https://{region}.storage.bunnycdn.com"
                else:
                    base_url = "https://storage.bunnycdn.com"

                download_url = f"{base_url}/{storage_zone}/{cdn_path}"

                async with httpx.AsyncClient(timeout=300) as client:
                    response = await client.get(
                        download_url,
                        headers={"AccessKey": settings.BUNNY_STORAGE_API_KEY},
                    )
                    response.raise_for_status()
                    with open(file_path, "wb") as f:
                        f.write(response.content)
            else:
                raise ValueError("Backup file not found and CDN not configured")

        # Parse DATABASE_URL for pg_restore
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

        parsed = urlparse(db_url)
        env = os.environ.copy()
        env["PGPASSWORD"] = parsed.password or ""

        db_name = parsed.path.lstrip("/")
        common_args = [
            "-h", parsed.hostname or "db",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "postgres",
        ]

        # Close existing connections via the async session
        await db.execute(text(
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid()"
        ))
        await db.commit()

        # pg_restore with clean + create
        cmd = [
            "pg_restore",
            *common_args,
            "-d", db_name,
            "--clean",
            "--if-exists",
            str(file_path),
        ]

        result = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=600
        )

        if result.returncode != 0 and "error" in result.stderr.lower():
            logger.warning(f"pg_restore warnings: {result.stderr}")

        logger.info(f"Database restored from: {backup.filename}")
        return {"status": "restored", "backup": backup.filename}

    @staticmethod
    async def _collect_database_metadata(db: AsyncSession) -> dict:
        """Collect database metadata for backup records."""
        metadata = {}
        try:
            # Database size
            result = await db.execute(
                text("SELECT pg_size_pretty(pg_database_size(current_database()))")
            )
            row = result.scalar()
            metadata["database_size"] = row

            # Table count
            result = await db.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
            )
            metadata["table_count"] = result.scalar()

            # PostgreSQL version
            result = await db.execute(text("SELECT version()"))
            metadata["pg_version"] = result.scalar()

        except Exception as e:
            metadata["error"] = str(e)

        return metadata
