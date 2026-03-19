from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import ConversationType
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.conversation import Conversation
from app.models.user_activity import UserActivity
from app.schemas.conversation import ConversationCreate, ConversationUpdate


async def create_conversation(
    db: AsyncSession, user_id: UUID, data: ConversationCreate
) -> Conversation:
    conversation = Conversation(
        user_id=user_id,
        business_id=data.business_id,
        title=data.title or "Nueva conversacion",
        conversation_type=data.conversation_type,
    )
    db.add(conversation)
    db.add(UserActivity(user_id=user_id, event_type="new_conversation",
                        metadata_={"type": data.conversation_type.value if data.conversation_type else None}))
    await db.flush()
    return conversation


async def get_conversations(
    db: AsyncSession,
    user_id: UUID,
    business_id: UUID | None = None,
    conversation_type: ConversationType | None = None,
) -> list[Conversation]:
    query = select(Conversation).where(
        Conversation.user_id == user_id,
        Conversation.is_archived == False,  # noqa: E712
    )
    if business_id:
        query = query.where(Conversation.business_id == business_id)
    if conversation_type:
        query = query.where(Conversation.conversation_type == conversation_type)

    result = await db.execute(query.order_by(Conversation.updated_at.desc()))
    return list(result.scalars().all())


async def get_conversation_with_messages(
    db: AsyncSession, conversation_id: UUID, user_id: UUID
) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")
    if conversation.user_id != user_id:
        raise ForbiddenError("Not your conversation")
    return conversation


async def update_conversation(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    data: ConversationUpdate,
) -> Conversation:
    conversation = await get_conversation_with_messages(
        db, conversation_id, user_id
    )
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(conversation, key, value)
    await db.flush()
    return conversation


async def delete_conversation(
    db: AsyncSession, conversation_id: UUID, user_id: UUID
) -> None:
    conversation = await get_conversation_with_messages(
        db, conversation_id, user_id
    )
    await db.delete(conversation)
