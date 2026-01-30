import uuid

from fastapi import APIRouter, Query

from app.api.deps import DB, CurrentUser
from app.core.constants import ConversationType
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)
from app.services import conversation_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    db: DB,
    current_user: CurrentUser,
    business_id: uuid.UUID | None = Query(None),
    conversation_type: ConversationType | None = Query(None),
):
    return await conversation_service.get_conversations(
        db, current_user.id, business_id, conversation_type
    )


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate, db: DB, current_user: CurrentUser
):
    return await conversation_service.create_conversation(
        db, current_user.id, data
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    return await conversation_service.get_conversation_with_messages(
        db, conversation_id, current_user.id
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: uuid.UUID,
    data: ConversationUpdate,
    db: DB,
    current_user: CurrentUser,
):
    return await conversation_service.update_conversation(
        db, conversation_id, current_user.id, data
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    await conversation_service.delete_conversation(
        db, conversation_id, current_user.id
    )
