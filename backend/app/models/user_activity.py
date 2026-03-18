import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User

# Tipos de evento válidos
EVENT_TYPES = (
    "login",
    "register",
    "new_conversation",
    "send_message",
    "calendar_created",
    "strategy_generated",
    "business_created",
    "business_updated",
    "business_deleted",
)


class UserActivity(UUIDMixin, Base):
    """
    Registra eventos de actividad de cada usuario.
    Soft-delete friendly: si el usuario se desactiva, sus actividades se conservan.
    Si se hace hard-delete del usuario, cascade elimina las actividades.
    """
    __tablename__ = "user_activities"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Tipo de evento: login, send_message, calendar_created, etc.
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Metadatos opcionales: {"conversation_id": "...", "model": "...", etc.}
    # JSONB en PostgreSQL, JSON en SQLite
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="activities")
