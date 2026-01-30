import uuid
from datetime import date, datetime

from pydantic import BaseModel


class ContentCalendarResponse(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    conversation_id: uuid.UUID | None
    title: str
    week_start_date: date
    week_end_date: date
    platform: str
    strategy_summary: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContentCalendarUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
