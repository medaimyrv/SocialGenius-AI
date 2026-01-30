import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.content_calendar import ContentCalendar
    from app.models.conversation import Conversation
    from app.models.user import User


class Business(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "businesses"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_audience: Mapped[str | None] = mapped_column(Text)
    brand_voice: Mapped[str | None] = mapped_column(String(100))
    website_url: Mapped[str | None] = mapped_column(String(500))
    instagram_handle: Mapped[str | None] = mapped_column(String(100))
    tiktok_handle: Mapped[str | None] = mapped_column(String(100))
    extra_context: Mapped[dict | None] = mapped_column(JSON)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="businesses")
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="business"
    )
    content_calendars: Mapped[list["ContentCalendar"]] = relationship(
        back_populates="business", cascade="all, delete-orphan"
    )
