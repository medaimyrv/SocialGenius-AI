import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.business import Business
    from app.models.content_piece import ContentPiece


class ContentCalendar(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "content_calendars"

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    week_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    strategy_summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="draft")

    # Relationships
    business: Mapped["Business"] = relationship(back_populates="content_calendars")
    content_pieces: Mapped[list["ContentPiece"]] = relationship(
        back_populates="calendar",
        cascade="all, delete-orphan",
        order_by="ContentPiece.scheduled_date, ContentPiece.scheduled_time",
    )
