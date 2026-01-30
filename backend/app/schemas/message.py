import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.constants import MessageRole


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    token_count: int | None
    model_used: str | None
    metadata_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
