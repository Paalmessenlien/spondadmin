"""
Member service for CRUD operations
"""
from typing import List, Optional, Dict, Any
import logging

from sqlalchemy import select, func, or_, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.models.group import Group
from app.models.group_member import GroupMember
from app.schemas.member import MemberUpdate, MemberFilters

logger = logging.getLogger(__name__)


class MemberService:
    """Service for member CRUD operations"""

    @staticmethod
    def _apply_group_filters(
        query,
        group_spond_id: Optional[str],
        subgroup_uid: Optional[str] = None,
    ):
        """
        Restrict a Member-based query by Spond group and/or subgroup.

        Group and subgroup filters share a single GroupMember join so combining
        them ANDs the conditions on the same association row (member must
        belong to the group AND have the subgroup recorded for that group).
        """
        if not group_spond_id and not subgroup_uid:
            return query
        query = query.join(GroupMember, GroupMember.member_id == Member.id)
        if group_spond_id:
            query = query.join(Group, Group.id == GroupMember.group_id).where(
                Group.spond_id == group_spond_id
            )
        if subgroup_uid:
            query = query.where(
                text("group_members.subgroup_uids::jsonb ? :sid").bindparams(sid=subgroup_uid)
            )
        return query

    # Backwards-compat shim used by analytics_service (group-only filter).
    @staticmethod
    def _apply_group_filter(query, group_spond_id: Optional[str]):
        return MemberService._apply_group_filters(query, group_spond_id)

    @staticmethod
    async def get_all(
        db: AsyncSession,
        filters: MemberFilters,
    ) -> tuple[List[Member], int]:
        """
        Get all members with optional filtering and pagination.
        """
        query = select(Member)

        conditions = []

        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Member.first_name.ilike(search_term),
                    Member.last_name.ilike(search_term),
                    Member.email.ilike(search_term),
                )
            )

        if filters.has_email is not None:
            if filters.has_email:
                conditions.append(Member.email.isnot(None))
            else:
                conditions.append(Member.email.is_(None))

        if filters.has_phone is not None:
            if filters.has_phone:
                conditions.append(Member.phone_number.isnot(None))
            else:
                conditions.append(Member.phone_number.is_(None))

        if filters.has_guardians is not None:
            if filters.has_guardians:
                conditions.append(Member.profile.isnot(None))
            else:
                conditions.append(Member.profile.is_(None))

        query = MemberService._apply_group_filters(
            query, filters.group_id, filters.subgroup_id
        )

        if conditions:
            query = query.where(*conditions)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        query = MemberService._apply_sort(query, filters.sort_by, filters.sort_order)
        query = query.offset(filters.skip).limit(filters.limit)

        result = await db.execute(query)
        members = result.scalars().unique().all()

        return list(members), total or 0

    @staticmethod
    def _apply_sort(query, sort_by: str, sort_order: str):
        descending = sort_order == "desc"

        def direction(col):
            return col.desc() if descending else col.asc()

        if sort_by == "email":
            # Push NULL emails to the end regardless of direction.
            return query.order_by(
                Member.email.is_(None).asc(),
                direction(Member.email),
                Member.last_name.asc(),
                Member.first_name.asc(),
            )
        if sort_by == "last_synced_at":
            return query.order_by(direction(Member.last_synced_at))
        if sort_by == "group_count":
            # Correlated subquery so we can sort without disturbing distinct rows.
            count_subq = (
                select(func.count(GroupMember.group_id))
                .where(GroupMember.member_id == Member.id)
                .correlate(Member)
                .scalar_subquery()
            )
            return query.order_by(
                direction(count_subq),
                Member.last_name.asc(),
                Member.first_name.asc(),
            )
        if sort_by == "subgroup_count":
            # Sum jsonb_array_length(subgroup_uids) across the member's associations.
            sub_count_subq = (
                select(
                    func.coalesce(
                        func.sum(
                            func.jsonb_array_length(
                                func.cast(GroupMember.subgroup_uids, JSONB)
                            )
                        ),
                        0,
                    )
                )
                .where(GroupMember.member_id == Member.id)
                .correlate(Member)
                .scalar_subquery()
            )
            return query.order_by(
                direction(sub_count_subq),
                Member.last_name.asc(),
                Member.first_name.asc(),
            )
        # Default: name.
        return query.order_by(
            direction(Member.last_name),
            direction(Member.first_name),
        )

    @staticmethod
    async def get_by_id(db: AsyncSession, member_id: int) -> Optional[Member]:
        result = await db.execute(
            select(Member).where(Member.id == member_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_spond_id(db: AsyncSession, spond_id: str) -> Optional[Member]:
        result = await db.execute(
            select(Member).where(Member.spond_id == spond_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        member_id: int,
        update_data: MemberUpdate,
    ) -> Optional[Member]:
        member = await MemberService.get_by_id(db, member_id)
        if not member:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(member, key, value)

        await db.flush()
        await db.refresh(member)

        logger.info(f"Updated member {member_id}")
        return member

    @staticmethod
    async def get_statistics(
        db: AsyncSession,
        group_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get member statistics, optionally scoped to a single Spond group.
        """

        def base_query(column_filter=None):
            q = select(func.count(func.distinct(Member.id)))
            if column_filter is not None:
                q = q.where(column_filter)
            return MemberService._apply_group_filter(q, group_id)

        total_members = (await db.execute(base_query())).scalar() or 0
        members_with_email = (
            await db.execute(base_query(Member.email.isnot(None)))
        ).scalar() or 0
        members_with_phone = (
            await db.execute(base_query(Member.phone_number.isnot(None)))
        ).scalar() or 0
        members_with_profile = (
            await db.execute(base_query(Member.profile.isnot(None)))
        ).scalar() or 0

        # Average groups per member: count associations per member, then average.
        per_member_counts = (
            select(func.count(GroupMember.group_id).label("group_count"))
            .group_by(GroupMember.member_id)
        )
        if group_id:
            member_ids_subq = (
                select(GroupMember.member_id)
                .join(Group, Group.id == GroupMember.group_id)
                .where(Group.spond_id == group_id)
            ).subquery()
            per_member_counts = per_member_counts.where(
                GroupMember.member_id.in_(select(member_ids_subq))
            )
        avg_result = await db.execute(
            select(func.avg(per_member_counts.subquery().c.group_count))
        )
        average_groups_per_member = float(avg_result.scalar() or 0.0)

        return {
            "total_members": total_members,
            "members_with_email": members_with_email,
            "members_with_phone": members_with_phone,
            "members_with_profile": members_with_profile,
            "average_groups_per_member": average_groups_per_member,
        }
