"""
Group synchronization service
Handles syncing groups from Spond API to local database
"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.sync_history import SyncHistory
from app.services.spond_service import SpondService

logger = logging.getLogger(__name__)


class GroupSyncService:
    """
    Service for synchronizing groups from Spond API to database
    """

    @staticmethod
    async def sync_groups(
        db: AsyncSession,
        spond_service: SpondService,
    ) -> Dict[str, int]:
        """
        Sync groups from Spond API to database

        Args:
            db: Database session
            spond_service: Spond service instance

        Returns:
            Dictionary with sync statistics
        """
        # Create sync history record
        sync_record = SyncHistory(
            sync_type="groups",
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(sync_record)
        await db.flush()

        stats = {
            "fetched": 0,
            "created": 0,
            "updated": 0,
            "errors": 0,
        }

        try:
            # Fetch groups from Spond API
            logger.info("Fetching groups from Spond API")
            groups_data = await spond_service.get_groups()

            stats["fetched"] = len(groups_data)
            logger.info(f"Fetched {len(groups_data)} groups from Spond")

            # Process each group
            for group_dict in groups_data:
                try:
                    await GroupSyncService._sync_single_group(db, group_dict, stats)
                except Exception as e:
                    logger.error(f"Error syncing group {group_dict.get('id')}: {e}")
                    stats["errors"] += 1

            # Update sync record
            sync_record.status = "completed"
            sync_record.success = True
            sync_record.completed_at = datetime.utcnow()
            sync_record.items_fetched = stats["fetched"]
            sync_record.items_created = stats["created"]
            sync_record.items_updated = stats["updated"]

            await db.flush()

            logger.info(
                f"Group sync completed: {stats['created']} created, "
                f"{stats['updated']} updated, {stats['errors']} errors"
            )

            return stats

        except Exception as e:
            logger.error(f"Group sync failed: {e}")

            # Update sync record with error
            sync_record.status = "failed"
            sync_record.success = False
            sync_record.completed_at = datetime.utcnow()
            sync_record.error_message = str(e)

            await db.flush()
            raise

    @staticmethod
    async def _sync_single_group(
        db: AsyncSession,
        group_dict: Dict[str, Any],
        stats: Dict[str, int],
    ) -> None:
        """
        Sync a single group to database

        Args:
            db: Database session
            group_dict: Group data from Spond API
            stats: Statistics dictionary to update
        """
        spond_id = group_dict.get("id")
        if not spond_id:
            logger.warning("Group missing ID, skipping")
            return

        # Check if group exists
        result = await db.execute(
            select(Group).where(Group.spond_id == spond_id)
        )
        existing_group = result.scalar_one_or_none()

        # Extract group data
        now = datetime.utcnow()
        group_data = {
            "spond_id": spond_id,
            "name": group_dict.get("name", ""),
            "description": group_dict.get("description"),
            "roles": group_dict.get("roles"),
            "subgroups": group_dict.get("subGroups", []),
            "raw_data": group_dict,
            "last_synced_at": now,
        }

        if existing_group:
            # Update existing group
            for key, value in group_data.items():
                setattr(existing_group, key, value)
            existing_group.updated_at = now
            stats["updated"] += 1
            logger.debug(f"Updated group: {group_data['name']}")
        else:
            # Create new group
            group_data["created_at"] = now
            group_data["updated_at"] = now
            new_group = Group(**group_data)
            db.add(new_group)
            stats["created"] += 1
            logger.debug(f"Created group: {group_data['name']}")

        await db.flush()
