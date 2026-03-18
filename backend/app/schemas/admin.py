from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr


# ── Usuarios ──────────────────────────────────────────────────────────────────

class AdminUserListItem(BaseModel):
    """Fila en la tabla de usuarios del panel admin."""
    id: UUID
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    # Contadores calculados en la query
    total_conversations: int = 0
    total_messages: int = 0
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}


class AdminUserDetail(AdminUserListItem):
    """Detalle completo de un usuario."""
    businesses_count: int = 0
    calendars_count: int = 0


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Actividad ─────────────────────────────────────────────────────────────────

class ActivityItem(BaseModel):
    id: UUID
    user_id: UUID
    user_email: str | None = None
    event_type: str
    metadata_: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityListResponse(BaseModel):
    items: list[ActivityItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── Acciones sobre usuarios ───────────────────────────────────────────────────

class AdminActionResponse(BaseModel):
    ok: bool
    message: str
