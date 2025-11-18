"""
Member synchronization service
Handles syncing members from Spond API to local database
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.models.group import Group
from app.models.sync_history import SyncHistory
from app.services.spond_service import SpondService

logger = logging.getLogger(__name__)


class MemberSyncService:
    """
    Service for synchronizing members from Spond API to database
    """

    @staticmethod
    async def sync_members(
        db: AsyncSession,
        spond_service: SpondService,
        group_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Sync members from Spond API to database

        Note: Members are synced from groups, so we need to iterate through groups

        Args:
            db: Database session
            spond_service: Spond service instance
            group_id: Optional specific group ID to sync members from

        Returns:
            Dictionary with sync statistics
        """
        # Create sync history record
        sync_record = SyncHistory(
            sync_type="members",
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
            # Get groups to extract members from
            if group_id:
                # Fetch specific group
                logger.info(f"Fetching members from group {group_id}")
                group_data = await spond_service.get_group(group_id)
                groups_data = [group_data] if group_data else []
            else:
                # Fetch all groups
                logger.info("Fetching members from all groups")
                groups_data = await spond_service.get_groups()

            logger.info(f"Processing {len(groups_data)} groups for member sync")

            # Process each group's members
            member_ids_seen = set()
            for group_dict in groups_data:
                try:
                    members_list = group_dict.get("members", [])

                    for member_dict in members_list:
                        try:
                            # Track unique members to avoid counting duplicates
                            member_id = member_dict.get("id") or member_dict.get("profile", {}).get("id")
                            if member_id and member_id not in member_ids_seen:
                                member_ids_seen.add(member_id)
                                stats["fetched"] += 1

                                await MemberSyncService._sync_single_member(
                                    db, member_dict, group_dict, stats
                                )
                        except Exception as e:
                            logger.error(f"Error syncing member: {e}")
                            stats["errors"] += 1

                except Exception as e:
                    logger.error(f"Error processing group {group_dict.get('id')}: {e}")
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
                f"Member sync completed: {stats['created']} created, "
                f"{stats['updated']} updated, {stats['errors']} errors"
            )

            return stats

        except Exception as e:
            logger.error(f"Member sync failed: {e}")

            # Update sync record with error
            sync_record.status = "failed"
            sync_record.success = False
            sync_record.completed_at = datetime.utcnow()
            sync_record.error_message = str(e)

            await db.flush()
            raise

    @staticmethod
    async def _sync_single_member(
        db: AsyncSession,
        member_dict: Dict[str, Any],
        group_dict: Dict[str, Any],
        stats: Dict[str, int],
    ) -> None:
        """
        Sync a single member to database

        Args:
            db: Database session
            member_dict: Member data from Spond API
            group_dict: Group data (for association)
            stats: Statistics dictionary to update
        """
        # Extract member ID (can be at different levels in the structure)
        spond_id = member_dict.get("id")
        profile = member_dict.get("profile", {})
        profile_id = profile.get("id")

        # Use whichever ID is available
        if not spond_id and profile_id:
            spond_id = profile_id

        if not spond_id:
            logger.warning("Member missing ID, skipping")
            return

        # Check if member exists
        result = await db.execute(
            select(Member).where(Member.spond_id == spond_id)
        )
        existing_member = result.scalar_one_or_none()

        # Extract member data
        first_name = profile.get("firstName", member_dict.get("firstName", ""))
        last_name = profile.get("lastName", member_dict.get("lastName", ""))

        # Extract role and subgroup UIDs
        role_uids = member_dict.get("roles", [])
        subgroup_uids = member_dict.get("subGroups", [])

        # Get member created time and parse it
        created_time_str = member_dict.get("createdTime")
        created_time = None
        if created_time_str:
            try:
                # Parse ISO format datetime string
                from dateutil import parser
                created_time = parser.parse(created_time_str)
            except Exception:
                logger.warning(f"Failed to parse created time: {created_time_str}")

        now = datetime.utcnow()
        member_data = {
            "spond_id": spond_id,
            "group_id": group_dict.get("id") if group_dict else None,
            "first_name": first_name,
            "last_name": last_name,
            "email": profile.get("email"),
            "phone_number": profile.get("phoneNumber"),
            "profile": profile if profile else None,
            "member_created_time": created_time,
            "role_uids": role_uids if role_uids else [],
            "subgroup_uids": subgroup_uids if subgroup_uids else [],
            "fields": member_dict.get("fields", {}),
            "raw_data": member_dict,
            "last_synced_at": now,
        }

        if existing_member:
            # Update existing member
            for key, value in member_data.items():
                setattr(existing_member, key, value)
            existing_member.updated_at = now
            stats["updated"] += 1
            logger.debug(f"Updated member: {first_name} {last_name}")
        else:
            # Create new member
            member_data["created_at"] = now
            member_data["updated_at"] = now
            new_member = Member(**member_data)
            db.add(new_member)
            stats["created"] += 1
            logger.debug(f"Created member: {first_name} {last_name}")

        await db.flush()
