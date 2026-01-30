import json
from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.ai.engine import AIEngine
from app.core.constants import ConversationType, MessageRole
from app.core.exceptions import NotFoundError
from app.models.business import Business
from app.models.conversation import Conversation
from app.models.message import Message

ai_engine = AIEngine()


async def send_message_and_stream(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    content: str,
) -> AsyncGenerator[str, None]:
    # Load conversation with messages
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")

    # Load business context if linked
    business = None
    if conversation.business_id:
        biz_result = await db.execute(
            select(Business).where(Business.id == conversation.business_id)
        )
        business = biz_result.scalar_one_or_none()

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=content,
    )
    db.add(user_message)
    await db.flush()

    # Build message history for AI
    messages_for_ai = [
        {"role": msg.role.value, "content": msg.content}
        for msg in conversation.messages
    ]
    messages_for_ai.append({"role": "user", "content": content})

    # Stream AI response
    full_response = ""
    model_used = ""

    async for chunk_data in ai_engine.stream_response(
        conversation_type=conversation.conversation_type,
        messages=messages_for_ai,
        business=business,
    ):
        if isinstance(chunk_data, dict):
            model_used = chunk_data.get("model", "")
            continue
        full_response += chunk_data
        yield f"data: {json.dumps({'content': chunk_data})}\n\n"

    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=full_response,
        model_used=model_used,
    )
    db.add(assistant_message)
    await db.flush()

    yield f"data: {json.dumps({'done': True})}\n\n"
