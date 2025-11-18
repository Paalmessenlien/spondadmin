"""
Member service for CRUD operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.schemas.member import MemberUpdate, MemberFilters

logger = logging.getLogger(__name__)


class MemberService:
    """Service for member CRUD operations"""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        filters: MemberFilters,
    ) -> tuple[List[Member], int]:
        """
        Get all members with optional filtering and pagination

        Args:
            db: Database session
            filters: Filter parameters

        Returns:
            Tuple of (members list, total count)
        """
        # Build base query
        query = select(Member)

        # Apply filters
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
            # Guardians are stored in the profile JSON field
            # This filter checks if profile exists (which would contain guardian info if any)
            if filters.has_guardians:
                conditions.append(Member.profile.isnot(None))
            else:
                conditions.append(Member.profile.is_(None))

        # Apply all conditions
        if conditions:
            query = query.where(*conditions)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting and pagination
        query = query.order_by(Member.last_name, Member.first_name)
        query = query.offset(filters.skip).limit(filters.limit)

        # Execute query
        result = await db.execute(query)
        members = result.scalars().all()

        return list(members), total or 0

    @staticmethod
    async def get_by_id(db: AsyncSession, member_id: int) -> Optional[Member]:
        """
        Get member by ID

        Args:
            db: Database session
            member_id: Member ID

        Returns:
            Member or None if not found
        """
        result = await db.execute(
            select(Member).where(Member.id == member_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_spond_id(db: AsyncSession, spond_id: str) -> Optional[Member]:
        """
        Get member by Spond ID

        Args:
            db: Database session
            spond_id: Spond member ID

        Returns:
            Member or None if not found
        """
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
        """
        Update a member

        Args:
            db: Database session
            member_id: Member ID
            update_data: Update data

        Returns:
            Updated member or None if not found
        """
        member = await MemberService.get_by_id(db, member_id)
        if not member:
            return None

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(member, key, value)

        await db.flush()
        await db.refresh(member)

        logger.info(f"Updated member {member_id}")
        return member

    @staticmethod
    async def get_statistics(db: AsyncSession) -> Dict[str, Any]:
        """
        Get member statistics

        Args:
            db: Database session

        Returns:
            Dictionary with statistics
        """
        # Total members
        total_result = await db.execute(select(func.count(Member.id)))
        total_members = total_result.scalar() or 0

        # Members with email
        with_email_result = await db.execute(
            select(func.count(Member.id)).where(Member.email.isnot(None))
        )
        members_with_email = with_email_result.scalar() or 0

        # Members with phone
        with_phone_result = await db.execute(
            select(func.count(Member.id)).where(Member.phone_number.isnot(None))
        )
        members_with_phone = with_phone_result.scalar() or 0

        # Members with profile
        with_profile_result = await db.execute(
            select(func.count(Member.id)).where(Member.profile.isnot(None))
        )
        members_with_profile = with_profile_result.scalar() or 0

        return {
            "total_members": total_members,
            "members_with_email": members_with_email,
            "members_with_phone": members_with_phone,
            "members_with_profile": members_with_profile,
            "average_groups_per_member": 0.0,  # Would need to calculate from group_id field
        }
