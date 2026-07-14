"""
Access control tables: reusable access groups and editable role defaults.

* ``AccessGroup`` — a named, reusable bundle of ``{role + modules}``. A user
  is assigned to at most one group (``admins.access_group_id``); the link is
  live, so editing a group re-resolves its members' module access. The group's
  role is *copied* onto members (kept in ``admins.role`` so all existing role
  guards keep working) and propagated when the group's role changes.

* ``RoleModuleDefault`` — the default module set per built-in role, moved out of
  code into the DB so admins can edit it in the UI. One row per role.
"""
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.admin import Admin


class AccessGroup(Base, TimestampMixin):
    """A reusable access preset assigned to users."""
    __tablename__ = "access_groups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # The role this group confers (view-vs-edit level). Copied onto members.
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="viewer")
    # The module keys this group grants (see app/core/modules.py).
    modules: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    members: Mapped[List["Admin"]] = relationship(
        "Admin", back_populates="access_group"
    )


class RoleModuleDefault(Base, TimestampMixin):
    """Editable default module set for one built-in role."""
    __tablename__ = "role_module_defaults"

    role: Mapped[str] = mapped_column(String(20), primary_key=True)
    modules: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
