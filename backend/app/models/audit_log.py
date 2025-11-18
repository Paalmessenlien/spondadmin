"""
Audit log model for tracking admin actions
"""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """
    Track all admin actions for security and compliance
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Admin who performed the action
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"), nullable=False, index=True)

    # Action details
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)  # event, member, group, etc.
    resource_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)

    # Action metadata
    description: Mapped[str] = mapped_column(Text, nullable=True)
    changes: Mapped[dict] = mapped_column(JSON, nullable=True)  # Before/after data

    # Request metadata
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)

    # Timestamp
    performed_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} on {self.resource_type} by admin {self.admin_id}>"
