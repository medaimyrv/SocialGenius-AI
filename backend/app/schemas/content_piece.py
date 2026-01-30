import uuid
from datetime import date, datetime, time

from pydantic import BaseModel

from app.core.constants import ContentFormat


class ContentPieceResponse(BaseModel):
    id: uuid.UUID
    calendar_id: uuid.UUID
    platform: str
    content_format: ContentFormat
    topic: str
    caption: str
    hashtags: list[str] | None
    visual_description: str | None
    hook: str | None
    call_to_action: str | None
    scheduled_date: date
    scheduled_time: time | None
    day_of_week: str
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContentPieceUpdate(BaseModel):
    caption: str | None = None
    hashtags: list[str] | None = None
    visual_description: str | None = None
    hook: str | None = None
    call_to_action: str | None = None
    scheduled_time: time | None = None
    notes: str | None = None
    status: str | None = None
