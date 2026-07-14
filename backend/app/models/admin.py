"""
Admin user model for authentication
"""
from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.access_group import AccessGroup


class UserRole(str, PyEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    # Treasurer: reviews/approves/marks-paid expense reimbursements (utlegg).
    KASSERER = "kasserer"


class Admin(Base, TimestampMixin):
    """
    Admin user model for the admin interface
    """
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    clerk_user_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), default=UserRole.VIEWER.value, nullable=False,
        server_default="viewer"
    )
    # Per-user module allow-list (see app/core/modules.py). Resolution order
    # is: explicit ``modules`` > assigned ``access_group`` > role default.
    #   NULL      → not customised; inherit from group or role default.
    #   [ "..." ] → explicit override list of sidebar modules.
    # Role still governs view-vs-edit; this only governs *which* modules.
    modules: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Optional assignment to a reusable access group. SET NULL so deleting a
    # group leaves its members intact (they fall back to role defaults).
    access_group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("access_groups.id", ondelete="SET NULL"), nullable=True, index=True
    )
    access_group: Mapped[Optional["AccessGroup"]] = relationship(
        "AccessGroup", back_populates="members", lazy="selectin"
    )

    @property
    def access_group_name(self) -> Optional[str]:
        """Convenience for API responses (access_group is selectin-loaded)."""
        return self.access_group.name if self.access_group else None

    def __repr__(self) -> str:
        return f"<Admin {self.username} ({self.email})>"
