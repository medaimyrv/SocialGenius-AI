import uuid
from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, JSON, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ContentFormat
from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.content_calendar import ContentCalendar


class ContentPiece(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "content_pieces"

    calendar_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_calendars.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    content_format: Mapped[ContentFormat] = mapped_column(
        SAEnum(ContentFormat), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[list[str] | None] = mapped_column(JSON)
    visual_description: Mapped[str | None] = mapped_column(Text)
    hook: Mapped[str | None] = mapped_column(String(500))
    call_to_action: Mapped[str | None] = mapped_column(String(500))
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_time: Mapped[time | None] = mapped_column(Time)
    day_of_week: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="draft")

    # Relationships
    calendar: Mapped["ContentCalendar"] = relationship(
        back_populates="content_pieces"
    )
