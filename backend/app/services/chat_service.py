import json
import logging
import re
from collections.abc import AsyncGenerator
from datetime import date, time, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.ai.engine import AIEngine
from app.core.constants import ContentFormat, ConversationType, MessageRole
from app.core.exceptions import NotFoundError
from app.models.business import Business
from app.models.content_calendar import ContentCalendar
from app.models.content_piece import ContentPiece
from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger(__name__)

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

    # Build message history for AI (from previously loaded messages)
    messages_for_ai = [
        {"role": msg.role.value, "content": msg.content}
        for msg in conversation.messages
    ]
    # Add current user message
    messages_for_ai.append({"role": "user", "content": content})

    # Save user message to DB
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=content,
    )
    db.add(user_message)
    await db.flush()

    # Stream AI response
    full_response = ""
    model_used = ""

    logger.info(f"Starting AI stream | conversation={conversation_id} type={conversation.conversation_type} business={business.name if business else None}")

    try:
        chunk_count = 0
        async for chunk_data in ai_engine.stream_response(
            conversation_type=conversation.conversation_type,
            messages=messages_for_ai,
            business=business,
        ):
            if isinstance(chunk_data, dict):
                model_used = chunk_data.get("model", "")
                logger.info(f"Using model: {model_used}")
                continue
            full_response += chunk_data
            chunk_count += 1
            if chunk_count == 1:
                logger.info("First chunk received from HuggingFace ✓")
            yield f"data: {json.dumps({'content': chunk_data})}\n\n"
        logger.info(f"Stream complete | chunks={chunk_count} total_chars={len(full_response)}")
    except Exception as e:
        logger.error(f"Error streaming AI response: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

    # Save assistant message
    if full_response:
        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=full_response,
            model_used=model_used,
        )
        db.add(assistant_message)
        await db.flush()

        # Auto-create calendar record for calendar conversations
        if (
            conversation.conversation_type == ConversationType.CALENDAR_CREATION
            and conversation.business_id
        ):
            await _save_calendar_from_response(
                db, conversation, full_response
            )

    yield f"data: {json.dumps({'done': True})}\n\n"




_DAY_NAME_TO_OFFSET = {
    "lunes": 0,
    "martes": 1, "martés": 1,
    "miércoles": 2, "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5, "sabado": 5,
    "domingo": 6,
}

# Canonical display names (with accents) for DB storage
_DAY_CANONICAL = {
    0: "Lunes", 1: "Martes", 2: "Miércoles",
    3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo",
}

_PLATFORM_MAP = {
    "instagram": "instagram",
    "tiktok": "tiktok",
}

_FORMAT_MAP = {
    "reel": ContentFormat.REEL,
    "reels": ContentFormat.REEL,
    "carrusel": ContentFormat.CAROUSEL,
    "carousel": ContentFormat.CAROUSEL,
    "imagen": ContentFormat.SINGLE_IMAGE,
    "single_image": ContentFormat.SINGLE_IMAGE,
    "foto": ContentFormat.SINGLE_IMAGE,
    "story": ContentFormat.STORY,
    "stories": ContentFormat.STORY,
    "historia": ContentFormat.STORY,
    "video": ContentFormat.TIKTOK_VIDEO,
    "tiktok_video": ContentFormat.TIKTOK_VIDEO,
    "live": ContentFormat.LIVE,
    "directo": ContentFormat.LIVE,
}


def _extract_field(block: str, name: str) -> str | None:
    """Extract a field value handling all Mistral formatting variants:
    **FIELD**: value  |  *FIELD*: value  |  FIELD: value  |  FIELD:* value  |  * **FIELD**: value
    """
    m = re.search(
        # Match the field name with optional surrounding asterisks
        rf"(?:\*{{0,2}}){re.escape(name)}(?:\*{{0,2}})\s*[_:]{{1,2}}\*?\s*(.+?)"
        # Stop at next field: newline + optional bullet/spaces + optional ** + 2+ uppercase letters
        rf"(?=\n\s*[\*\-]?\s*(?:\*{{0,2}})[A-ZÁÉÍÓÚÑ]{{2,}}(?:\*{{0,2}})\s*[_:]{{1,2}}\*?|\Z)",
        block,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None
    val = m.group(1).strip()
    # Strip markdown bullets and surrounding asterisks/quotes
    val = re.sub(r"^[\*\-\s\"]+|[\*\s\"]+$", "", val).strip()
    return val if val else None


_DAY_PATTERN = (
    r"Lunes|Mart[eé]s|Mi[eé]rcoles|Jueves|Viernes|S[aá]bado|Domingo"
)


def _split_into_post_blocks(text: str) -> list[str]:
    """Split AI response into per-post blocks.

    Strategy: first split by --- separators, then re-split any block that
    contains multiple day names (handles cases where the AI omits separators).
    """
    # Primary split: --- separators
    rough_blocks = re.split(r"(?m)^\s*-{3,}\s*$", text)

    blocks = []
    for block in rough_blocks:
        # Count how many day names appear in this block
        day_hits = list(re.finditer(
            rf"(?:^|\n)\s*[\*\#]{{0,3}}\s*(?:{_DAY_PATTERN})\b",
            block,
            re.IGNORECASE,
        ))
        if len(day_hits) <= 1:
            blocks.append(block)
        else:
            # Re-split at each day-name heading
            sub_blocks = re.split(
                rf"(?=(?:^|\n)\s*[\*\#]{{0,3}}\s*(?:{_DAY_PATTERN})\b)",
                block,
                flags=re.IGNORECASE,
            )
            blocks.extend(sub_blocks)

    return blocks


def _parse_calendar_blocks(ai_response: str, week_start: date) -> list[dict]:
    """Flexible parser that handles inconsistent Mistral-7B output formats."""
    pieces = []
    blocks = _split_into_post_blocks(ai_response)

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 30:
            continue

        # --- Find day name (handles accents, typos like "Martés") ---
        day_match = re.search(
            r"\b(Lunes|Mart[eé]s|Mi[eé]rcoles|Jueves|Viernes|S[aá]bado|Domingo)\b",
            block,
            re.IGNORECASE,
        )
        if not day_match:
            continue

        day_raw = day_match.group(1).lower()
        day_offset = _DAY_NAME_TO_OFFSET.get(day_raw)
        if day_offset is None:
            continue

        # --- Find platform ---
        plat_match = re.search(r"\b(Instagram|TikTok)\b", block, re.IGNORECASE)
        if plat_match:
            platform = plat_match.group(1).lower()
        elif re.search(r"\b(Reel|Carrusel|Story|Stories)\b", block, re.IGNORECASE):
            platform = "instagram"
        else:
            platform = "instagram"  # default to instagram when ambiguous

        # --- Find content format ---
        fmt_match = re.search(
            r"\b(Reel|Reels|Carrusel|Carousel|Imagen|Foto|Story|Stories|Historia|Video|Live|Directo)\b",
            block,
            re.IGNORECASE,
        )
        format_raw = fmt_match.group(1).lower() if fmt_match else "imagen"
        content_format = _FORMAT_MAP.get(format_raw, ContentFormat.SINGLE_IMAGE)

        # --- Extract fields ---
        hora_str = _extract_field(block, "HORA")
        scheduled_time = None
        if hora_str:
            t_match = re.search(r"(\d{1,2}:\d{2})", hora_str)
            if t_match:
                try:
                    scheduled_time = time.fromisoformat(t_match.group(1))
                except ValueError:
                    pass

        hashtags_raw = _extract_field(block, "HASHTAGS")
        hashtags = re.findall(r"#\w+", hashtags_raw) if hashtags_raw else []

        topic = (_extract_field(block, "TEMA") or "")[:500]
        caption = _extract_field(block, "CAPTION") or ""
        hook = (_extract_field(block, "GANCHO") or "")[:500]
        visual = _extract_field(block, "VISUAL")
        cta = (_extract_field(block, "CTA") or "")[:500]

        if not topic and not caption:
            continue

        pieces.append({
            "platform": platform,
            "content_format": content_format,
            "topic": topic,
            "caption": caption,
            "hook": hook,
            "hashtags": hashtags,
            "visual_description": visual,
            "call_to_action": cta,
            "scheduled_date": week_start + timedelta(days=day_offset),
            "scheduled_time": scheduled_time,
            "day_of_week": _DAY_CANONICAL[day_offset],
        })

    return pieces


async def _save_calendar_from_response(
    db: AsyncSession,
    conversation: Conversation,
    ai_response: str,
) -> None:
    """Create a ContentCalendar and ContentPiece records from the AI's calendar response."""
    try:
        today = date.today()
        # Find next Monday
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        week_start = today + timedelta(days=days_until_monday)
        week_end = week_start + timedelta(days=6)

        # Extract a summary from the first non-empty line
        lines = [l.strip() for l in ai_response.split("\n") if l.strip() and not l.startswith("#")]
        summary = lines[0][:500] if lines else "Calendario generado por IA"

        calendar = ContentCalendar(
            business_id=conversation.business_id,
            conversation_id=conversation.id,
            title=f"Calendario {week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m/%Y')}",
            week_start_date=week_start,
            week_end_date=week_end,
            platform="instagram,tiktok",
            strategy_summary=summary,
            status="draft",
        )
        db.add(calendar)
        await db.flush()
        logger.info(f"Calendar created: {calendar.id}")

        # Parse and save content pieces
        parsed_pieces = _parse_calendar_blocks(ai_response, week_start)
        for piece_data in parsed_pieces:
            piece = ContentPiece(calendar_id=calendar.id, **piece_data)
            db.add(piece)

        await db.flush()
        logger.info(f"Saved {len(parsed_pieces)} content pieces for calendar {calendar.id}")
    except Exception as e:
        logger.error(f"Failed to save calendar: {e}", exc_info=True)
