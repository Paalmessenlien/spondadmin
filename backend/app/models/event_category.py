"""
Event category model for classifying events by title patterns
"""
from typing import Optional
from sqlalchemy import String, Text, Boolean, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class EventCategory(Base, TimestampMixin):
    """
    Event category model for classifying events by title patterns.

    Attributes:
        id: Primary key
        name: Category name (e.g., "Training", "Match")
        description: Optional detailed description
        color: Hex color code for UI display (e.g., "#3B82F6")
        icon: Heroicon identifier (e.g., "i-heroicons-academic-cap")
        pattern_rules: JSON field containing pattern matching rules
        priority: Order for pattern matching (lower = higher priority)
        is_active: Whether this category is currently active
        is_default: Whether this is the default fallback category

    Pattern rules JSON structure:
        {
            "patterns": [
                {
                    "type": "contains|starts_with|ends_with|regex",
                    "value": "search_string",
                    "case_insensitive": true|false
                }
            ]
        }
    """
    __tablename__ = "event_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(50), nullable=False, default="#6B7280")
    icon: Mapped[str] = mapped_column(String(100), nullable=False, default="i-heroicons-tag")
    pattern_rules: Mapped[dict] = mapped_column(JSON, nullable=False, default={"patterns": []})
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    events = relationship("Event", back_populates="category")

    def __repr__(self) -> str:
        return f"<EventCategory(id={self.id}, name='{self.name}', priority={self.priority})>"
