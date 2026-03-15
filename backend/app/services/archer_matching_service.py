"""
Archer matching service - links bueskyting.no archers to Spond members
"""
import logging
import unicodedata
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.models.archer_profile import ArcherProfile
from app.models.unmatched_archer import UnmatchedArcher
from app.models.competition_result import CompetitionResult
from app.models.archer_statistics import ArcherStatistics

logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    """Normalize name for comparison: lowercase, strip accents, trim."""
    name = name.lower().strip()
    # Remove accents
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _name_similarity(name1: str, name2: str) -> float:
    """Compute name similarity score (0-100). Uses rapidfuzz if available, else basic."""
    try:
        from rapidfuzz import fuzz
        n1 = _normalize_name(name1)
        n2 = _normalize_name(name2)
        # Use token_sort_ratio to handle "First Last" vs "Last, First"
        return fuzz.token_sort_ratio(n1, n2)
    except ImportError:
        # Fallback: exact normalized match
        n1 = _normalize_name(name1)
        n2 = _normalize_name(name2)
        if n1 == n2:
            return 100.0
        # Simple word overlap
        words1 = set(n1.split())
        words2 = set(n2.split())
        if not words1 or not words2:
            return 0.0
        overlap = len(words1 & words2)
        return (overlap / max(len(words1), len(words2))) * 100


class ArcherMatchingService:
    """Service for matching bueskyting.no archers to Spond members."""

    @staticmethod
    async def auto_match_archers(db: AsyncSession) -> dict:
        """
        Attempt to automatically match unmatched archers to members by name similarity.
        Returns stats on matches found.
        """
        # Get unmatched, non-dismissed archers
        result = await db.execute(
            select(UnmatchedArcher).where(
                UnmatchedArcher.dismissed == False,
                UnmatchedArcher.suggested_spond_id.is_(None),
            )
        )
        unmatched = result.scalars().all()

        if not unmatched:
            return {"checked": 0, "matched": 0, "suggested": 0}

        # Get all members
        members_result = await db.execute(select(Member))
        members = members_result.scalars().all()

        matched = 0
        suggested = 0

        for archer in unmatched:
            best_score = 0.0
            best_member = None

            for member in members:
                full_name = f"{member.first_name} {member.last_name}"
                score = _name_similarity(archer.name, full_name)
                if score > best_score:
                    best_score = score
                    best_member = member

            if best_member and best_score >= 95:
                # High confidence - auto-match
                await ArcherMatchingService.manual_match(
                    db, archer.bueskyting_id, best_member.spond_id
                )
                matched += 1
            elif best_member and best_score >= 75:
                # Suggest but don't auto-match
                archer.suggested_spond_id = best_member.spond_id
                archer.match_confidence = best_score
                archer.updated_at = datetime.now(timezone.utc)
                suggested += 1

        await db.flush()
        return {
            "checked": len(unmatched),
            "matched": matched,
            "suggested": suggested,
        }

    @staticmethod
    async def manual_match(db: AsyncSession, bueskyting_id: str, spond_id: str) -> dict:
        """
        Manually link a bueskyting.no archer to a Spond member.
        Sets bueskyting_id on ArcherProfile and updates all results/stats.
        """
        now = datetime.now(timezone.utc)

        # Get or create ArcherProfile
        profile_q = await db.execute(
            select(ArcherProfile).where(ArcherProfile.spond_id == spond_id)
        )
        profile = profile_q.scalar_one_or_none()

        if profile:
            profile.bueskyting_id = bueskyting_id
            profile.updated_at = now
        else:
            profile = ArcherProfile(
                spond_id=spond_id,
                bueskyting_id=bueskyting_id,
                created_at=now,
                updated_at=now,
            )
            db.add(profile)

        # Update all competition results for this archer
        await db.execute(
            CompetitionResult.__table__.update()
            .where(CompetitionResult.bueskyting_archer_id == bueskyting_id)
            .values(spond_id=spond_id)
        )

        # Update all statistics for this archer
        await db.execute(
            ArcherStatistics.__table__.update()
            .where(ArcherStatistics.bueskyting_archer_id == bueskyting_id)
            .values(spond_id=spond_id)
        )

        # Remove from unmatched list
        result = await db.execute(
            select(UnmatchedArcher).where(UnmatchedArcher.bueskyting_id == bueskyting_id)
        )
        unmatched = result.scalar_one_or_none()
        if unmatched:
            await db.delete(unmatched)

        await db.flush()
        return {"bueskyting_id": bueskyting_id, "spond_id": spond_id}

    @staticmethod
    async def dismiss_unmatched(db: AsyncSession, unmatched_id: int) -> None:
        """Mark an unmatched archer as dismissed."""
        result = await db.execute(
            select(UnmatchedArcher).where(UnmatchedArcher.id == unmatched_id)
        )
        unmatched = result.scalar_one_or_none()
        if unmatched:
            unmatched.dismissed = True
            unmatched.updated_at = datetime.now(timezone.utc)
            await db.flush()

    @staticmethod
    async def get_unmatched(db: AsyncSession, include_dismissed: bool = False) -> List[UnmatchedArcher]:
        """Get all unmatched archers."""
        conditions = []
        if not include_dismissed:
            conditions.append(UnmatchedArcher.dismissed == False)

        query = select(UnmatchedArcher)
        if conditions:
            query = query.where(*conditions)
        query = query.order_by(UnmatchedArcher.name)

        result = await db.execute(query)
        return result.scalars().all()
