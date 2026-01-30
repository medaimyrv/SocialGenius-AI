import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.constants import ConversationType


class ConversationCreate(BaseModel):
    business_id: uuid.UUID | None = None
    title: str | None = "Nueva conversacion"
    conversation_type: ConversationType = ConversationType.GENERAL


class ConversationUpdate(BaseModel):
    title: str | None = None
    is_archived: bool | None = None


class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    business_id: uuid.UUID | None
    title: str
    conversation_type: ConversationType
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
