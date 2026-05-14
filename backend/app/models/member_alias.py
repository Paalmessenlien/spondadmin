"""
MemberAlias — maps an alias (typically trainer initials from the vaktliste
spreadsheet) to a Spond member. One member can have multiple aliases, but each
alias string is globally unique.
"""
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.member import Member


class MemberAlias(Base, TimestampMixin):
    __tablename__ = "member_aliases"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # e.g. "PME". We don't force uppercase at the DB layer — the API can
    # normalise on write.
    initials: Mapped[str] = mapped_column(
        String(16),
        unique=True,
        nullable=False,
        index=True,
    )

    # 'vaktliste' = imported from spreadsheet, 'manual' = entered in UI,
    # 'auto' = inferred (reserved for future heuristics).
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="manual",
        server_default="manual",
    )

    member: Mapped["Member"] = relationship()

    def __repr__(self) -> str:
        return f"<MemberAlias id={self.id} initials={self.initials!r} member_id={self.member_id}>"
