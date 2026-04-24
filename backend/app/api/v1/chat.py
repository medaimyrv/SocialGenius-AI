import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.deps import DB, CurrentUser
from app.main import limiter
from app.schemas.message import MessageCreate
from app.services.chat_service import send_message_and_stream
from app.services import usage_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{conversation_id}/messages")
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    conversation_id: uuid.UUID,
    data: MessageCreate,
    db: DB,
    current_user: CurrentUser,
):
    await usage_service.check_message_limit(db, current_user.id)
    return StreamingResponse(
        send_message_and_stream(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            content=data.content,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
