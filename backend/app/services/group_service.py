"""
Group service for CRUD operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.schemas.group import GroupUpdate, GroupFilters

logger = logging.getLogger(__name__)


class GroupService:
    """Service for group CRUD operations"""

    @staticmethod
    async def get_all(
        db: AsyncSession,
        filters: GroupFilters,
    ) -> tuple[List[Group], int]:
        """
        Get all groups with optional filtering and pagination

        Args:
            db: Database session
            filters: Filter parameters

        Returns:
            Tuple of (groups list, total count)
        """
        # Build base query
        query = select(Group)

        # Apply filters
        conditions = []

        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Group.name.ilike(search_term),
                    Group.description.ilike(search_term),
                )
            )

        if filters.has_subgroups is not None:
            if filters.has_subgroups:
                # Has subgroups (non-empty array)
                conditions.append(Group.subgroups.isnot(None))
            else:
                # No subgroups (null or empty array)
                conditions.append(
                    or_(
                        Group.subgroups.is_(None),
                        func.json_array_length(Group.subgroups) == 0
                    )
                )

        # Apply all conditions
        if conditions:
            query = query.where(*conditions)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting and pagination
        query = query.order_by(Group.name)
        query = query.offset(filters.skip).limit(filters.limit)

        # Execute query
        result = await db.execute(query)
        groups = result.scalars().all()

        return list(groups), total or 0

    @staticmethod
    async def get_by_id(db: AsyncSession, group_id: int) -> Optional[Group]:
        """
        Get group by ID

        Args:
            db: Database session
            group_id: Group ID

        Returns:
            Group or None if not found
        """
        result = await db.execute(
            select(Group).where(Group.id == group_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_spond_id(db: AsyncSession, spond_id: str) -> Optional[Group]:
        """
        Get group by Spond ID

        Args:
            db: Database session
            spond_id: Spond group ID

        Returns:
            Group or None if not found
        """
        result = await db.execute(
            select(Group).where(Group.spond_id == spond_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        group_id: int,
        update_data: GroupUpdate,
    ) -> Optional[Group]:
        """
        Update a group

        Args:
            db: Database session
            group_id: Group ID
            update_data: Update data

        Returns:
            Updated group or None if not found
        """
        group = await GroupService.get_by_id(db, group_id)
        if not group:
            return None

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(group, key, value)

        await db.flush()
        await db.refresh(group)

        logger.info(f"Updated group {group_id}")
        return group

    @staticmethod
    async def get_statistics(db: AsyncSession) -> Dict[str, Any]:
        """
        Get group statistics

        Args:
            db: Database session

        Returns:
            Dictionary with statistics
        """
        # Total groups
        total_result = await db.execute(select(func.count(Group.id)))
        total_groups = total_result.scalar() or 0

        # Groups with subgroups
        with_subgroups_result = await db.execute(
            select(func.count(Group.id)).where(
                Group.subgroups.isnot(None)
            )
        )
        groups_with_subgroups = with_subgroups_result.scalar() or 0

        # Count total subgroups
        # This is approximate since subgroups are stored as JSON
        total_subgroups = 0
        groups_result = await db.execute(select(Group.subgroups))
        for (subgroups,) in groups_result:
            if subgroups:
                total_subgroups += len(subgroups)

        return {
            "total_groups": total_groups,
            "groups_with_subgroups": groups_with_subgroups,
            "total_subgroups": total_subgroups,
            "average_members_per_group": 0.0,  # Updated when members are synced
        }
