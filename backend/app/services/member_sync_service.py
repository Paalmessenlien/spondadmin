"""
Member synchronization service
Handles syncing members from Spond API to local database
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.models.group import Group
from app.models.group_member import GroupMember
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

        Members are fetched per Spond group. A member that exists in multiple
        Spond groups produces one row in `members` and one row per (member,
        group) pair in `group_members`.

        Args:
            db: Database session
            spond_service: Spond service instance
            group_id: Optional specific Spond group ID to sync members from

        Returns:
            Dictionary with sync statistics
        """
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
            if group_id:
                logger.info(f"Fetching members from group {group_id}")
                group_data = await spond_service.get_group(group_id)
                groups_data = [group_data] if group_data else []
            else:
                logger.info("Fetching members from all groups")
                groups_data = await spond_service.get_groups()

            logger.info(f"Processing {len(groups_data)} groups for member sync")

            # Build {spond_id -> groups.id} lookup once to avoid N+1 queries.
            group_lookup = await MemberSyncService._build_group_lookup(db)

            member_ids_seen = set()
            for group_dict in groups_data:
                try:
                    spond_group_id = group_dict.get("id")
                    db_group_id = group_lookup.get(spond_group_id)
                    if db_group_id is None:
                        logger.warning(
                            f"Group {spond_group_id} not present in DB; "
                            f"run group sync before member sync. Skipping its members."
                        )
                        continue

                    members_list = group_dict.get("members", [])

                    for member_dict in members_list:
                        try:
                            spond_member_id = (
                                member_dict.get("id")
                                or member_dict.get("profile", {}).get("id")
                            )
                            if spond_member_id and spond_member_id not in member_ids_seen:
                                member_ids_seen.add(spond_member_id)
                                stats["fetched"] += 1

                            await MemberSyncService._sync_single_member(
                                db, member_dict, db_group_id, stats
                            )
                        except Exception as e:
                            logger.error(f"Error syncing member: {e}")
                            stats["errors"] += 1

                except Exception as e:
                    logger.error(f"Error processing group {group_dict.get('id')}: {e}")
                    stats["errors"] += 1

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

            sync_record.status = "failed"
            sync_record.success = False
            sync_record.completed_at = datetime.utcnow()
            sync_record.error_message = str(e)

            await db.flush()
            raise

    @staticmethod
    async def _build_group_lookup(db: AsyncSession) -> Dict[str, int]:
        """Map Spond group_id (string) -> groups.id (int) for fast FK resolution."""
        result = await db.execute(select(Group.spond_id, Group.id))
        return {spond_id: db_id for spond_id, db_id in result.all()}

    @staticmethod
    async def _sync_single_member(
        db: AsyncSession,
        member_dict: Dict[str, Any],
        db_group_id: int,
        stats: Dict[str, int],
    ) -> None:
        """
        Upsert a single member and their association to the given group.

        Args:
            db: Database session
            member_dict: Member data from Spond API
            db_group_id: surrogate `groups.id` for the group the member appears in
            stats: Statistics dictionary to update (Member-level only)
        """
        spond_id = member_dict.get("id")
        profile = member_dict.get("profile", {})
        profile_id = profile.get("id")

        if not spond_id and profile_id:
            spond_id = profile_id

        if not spond_id:
            logger.warning("Member missing ID, skipping")
            return

        result = await db.execute(
            select(Member).where(Member.spond_id == spond_id)
        )
        existing_member = result.scalar_one_or_none()

        first_name = profile.get("firstName", member_dict.get("firstName", ""))
        last_name = profile.get("lastName", member_dict.get("lastName", ""))

        role_uids = member_dict.get("roles", []) or []
        subgroup_uids = member_dict.get("subGroups", []) or []

        created_time_str = member_dict.get("createdTime")
        created_time = None
        if created_time_str:
            try:
                from dateutil import parser
                created_time = parser.parse(created_time_str)
                if created_time.tzinfo is not None:
                    created_time = created_time.astimezone(timezone.utc).replace(tzinfo=None)
            except Exception:
                logger.warning(f"Failed to parse created time: {created_time_str}")

        now = datetime.utcnow()
        member_data = {
            "spond_id": spond_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": profile.get("email"),
            "phone_number": profile.get("phoneNumber"),
            "profile": profile if profile else None,
            "member_created_time": created_time,
            "fields": member_dict.get("fields", {}),
            "raw_data": member_dict,
            "last_synced_at": now,
        }

        if existing_member:
            for key, value in member_data.items():
                setattr(existing_member, key, value)
            existing_member.updated_at = now
            # Only count as updated the first time we touch this member this sync.
            stats["updated"] += 1
            member_db_id = existing_member.id
            logger.debug(f"Updated member: {first_name} {last_name}")
        else:
            member_data["created_at"] = now
            member_data["updated_at"] = now
            new_member = Member(**member_data)
            db.add(new_member)
            await db.flush()  # populate new_member.id
            member_db_id = new_member.id
            stats["created"] += 1
            logger.debug(f"Created member: {first_name} {last_name}")

        # Upsert the (member, group) association with per-group role/subgroup data.
        assoc_result = await db.execute(
            select(GroupMember).where(
                GroupMember.member_id == member_db_id,
                GroupMember.group_id == db_group_id,
            )
        )
        assoc = assoc_result.scalar_one_or_none()

        if assoc:
            assoc.role_uids = role_uids
            assoc.subgroup_uids = subgroup_uids
            assoc.last_synced_at = now
            assoc.updated_at = now
        else:
            db.add(
                GroupMember(
                    member_id=member_db_id,
                    group_id=db_group_id,
                    role_uids=role_uids,
                    subgroup_uids=subgroup_uids,
                    last_synced_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )

        await db.flush()
