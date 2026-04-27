"""
Chat Service — Orquestador principal del flujo de conversación.

Responsabilidades:
  1. Recuperar el historial de la conversación (ventana deslizante de 20 mensajes).
  2. Buscar contexto RAG relevante para el mensaje del usuario.
  3. Construir el array de mensajes para el LLM en el orden correcto.
  4. Hacer streaming de la respuesta de HuggingFace al cliente via SSE.
  5. Persistir user_message + assistant_message en DB.
  6. Indexar ambos mensajes en RAG para memoria futura.
  7. Si el tipo es CALENDAR_CREATION, parsear la respuesta y crear el calendario.

El flujo de SSE (Server-Sent Events):
  - Se hace yield de cada chunk de texto a medida que llega del LLM.
  - Al final se hace yield de {"done": true}.
  - Si hay error se hace yield de {"error": "..."} y se termina.
"""
import json
import logging
import re
from collections.abc import AsyncGenerator
from datetime import date, time, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.engine import AIEngine
from app.core.constants import ContentFormat, ConversationType, MessageRole
from app.core.exceptions import NotFoundError
from app.models.business import Business
from app.models.content_calendar import ContentCalendar
from app.models.content_piece import ContentPiece
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user_activity import UserActivity
from app.services import rag_service

logger = logging.getLogger(__name__)

ai_engine = AIEngine()

# Máximo de mensajes del historial que se envían al LLM.
# Con 20 mensajes y respuestas de ~500 tokens, usamos ~10K tokens de contexto —
# bien por debajo del límite de Qwen2.5-72B (131K tokens).
MAX_HISTORY = 20


# ── Función principal ─────────────────────────────────────────────────────────

async def send_message_and_stream(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    content: str,
) -> AsyncGenerator[str, None]:
    """
    Procesa un mensaje del usuario y hace streaming de la respuesta de la IA.

    Es un generador asíncrono: cada yield es un chunk SSE listo para enviar
    al cliente. El caller (chat.py) lo envuelve en StreamingResponse.
    """
    # Cargar la conversación junto con todos sus mensajes en una sola query
    # (selectinload evita el N+1 que ocurriría si accediéramos a .messages después)
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,  # garantizar que pertenece al usuario
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise NotFoundError("Conversation not found")

    # Cargar el negocio vinculado — necesario para personalizar los prompts
    business = None
    if conversation.business_id:
        biz_result = await db.execute(
            select(Business).where(Business.id == conversation.business_id)
        )
        business = biz_result.scalar_one_or_none()

    # ── Paso 1: RAG — recuperar contexto semántico relevante ─────────────────
    rag_context = ""
    if conversation.business_id:
        try:
            rag_context = await rag_service.retrieve_context(
                db=db,
                business_id=str(conversation.business_id),
                query=content,
            )
        except Exception as e:
            # RAG es opcional — si falla, el chat sigue funcionando sin contexto extra
            logger.warning("RAG retrieval fallido (no crítico): %s", e)

    # ── Paso 2: construir el array de mensajes para el LLM ───────────────────
    # Solo enviamos los últimos MAX_HISTORY mensajes para controlar el uso de tokens.
    # Los mensajes más antiguos siguen en DB pero no se envían al LLM.
    messages_for_ai = [
        {"role": msg.role.value, "content": msg.content}
        for msg in conversation.messages[-MAX_HISTORY:]
    ]

    # El contexto RAG va JUSTO ANTES del mensaje actual del usuario, no al principio.
    # Si lo ponemos al inicio, el LLM lo lee sin el contexto conversacional previo
    # y la relevancia baja. Al final, el LLM tiene todo el historial para
    # entender qué parte del contexto RAG es aplicable.
    if rag_context:
        rag_injection = (
            f"[CONTEXTO RELEVANTE RECUPERADO]\n{rag_context}\n"
            "[Usa este contexto para dar respuestas más personalizadas y precisas.]"
        )
        messages_for_ai.append({"role": "system", "content": rag_injection})

    # El mensaje actual del usuario siempre va al final
    messages_for_ai.append({"role": "user", "content": content})

    # ── Paso 3: persistir el mensaje del usuario ANTES de hacer streaming ────
    # Guardamos el mensaje antes de llamar al LLM para que quede registrado
    # incluso si el streaming falla a mitad.
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=content,
    )
    db.add(user_message)
    db.add(UserActivity(
        user_id=user_id,
        event_type="send_message",
        metadata_={"conversation_id": str(conversation_id)},
    ))
    await db.flush()

    # ── Paso 4: streaming de la respuesta del LLM ────────────────────────────
    full_response = ""
    model_used = ""

    logger.info(
        "Iniciando stream | conversation=%s type=%s business=%s",
        conversation_id, conversation.conversation_type,
        business.name if business else None,
    )

    try:
        chunk_count = 0
        async for chunk_data in ai_engine.stream_response(
            conversation_type=conversation.conversation_type,
            messages=messages_for_ai,
            business=business,
        ):
            # El primer item del generador es un dict con metadatos del modelo
            if isinstance(chunk_data, dict):
                model_used = chunk_data.get("model", "")
                logger.info("Modelo en uso: %s", model_used)
                continue

            full_response += chunk_data
            chunk_count += 1
            if chunk_count == 1:
                logger.info("Primer chunk recibido de HuggingFace ✓")

            yield f"data: {json.dumps({'content': chunk_data})}\n\n"

        logger.info(
            "Stream completado | chunks=%d total_chars=%d",
            chunk_count, len(full_response),
        )
    except Exception as e:
        logger.error("Error en streaming de IA: %s", e, exc_info=True)
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

    # ── Paso 5: persistir la respuesta del asistente ─────────────────────────
    if full_response:
        db.add(Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=full_response,
            model_used=model_used,
        ))
        await db.flush()

        # ── Paso 6: indexar ambos mensajes en RAG (memoria futura) ───────────
        # Solo indexamos si hay negocio vinculado, ya que el RAG es por negocio.
        # Las respuestas del asistente se truncan a 4000 chars — lo suficiente
        # para capturar el contexto principal sin explotar la API de embeddings.
        if conversation.business_id:
            try:
                await rag_service.index_message(
                    db=db,
                    business_id=str(conversation.business_id),
                    conversation_id=str(conversation.id),
                    role="user",
                    content=content,
                )
                await rag_service.index_message(
                    db=db,
                    business_id=str(conversation.business_id),
                    conversation_id=str(conversation.id),
                    role="assistant",
                    content=full_response[:4000],
                )
            except Exception as e:
                logger.warning("RAG indexing fallido (no crítico): %s", e)

        # ── Paso 7: auto-crear calendario si aplica ───────────────────────────
        if (
            conversation.conversation_type == ConversationType.CALENDAR_CREATION
            and conversation.business_id
        ):
            await _save_calendar_from_response(db, conversation, full_response)

    yield f"data: {json.dumps({'done': True})}\n\n"


# ── Parser de calendarios ─────────────────────────────────────────────────────
#
# El LLM devuelve el calendario como texto libre con un formato semi-estructurado.
# Este parser extrae los campos de cada publicación con regex flexible que tolera
# variaciones de formato del modelo (asteriscos, dos puntos dobles, mayúsculas, etc.)
#
# Flujo:
#   texto del LLM → bloques por publicación → campos por bloque → ContentPiece dicts

_DAY_NAME_TO_OFFSET: dict[str, int] = {
    "lunes": 0,
    "martes": 1, "martés": 1,
    "miércoles": 2, "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5, "sabado": 5,
    "domingo": 6,
}

# Nombres canónicos con tilde para guardar en DB
_DAY_CANONICAL: dict[int, str] = {
    0: "Lunes", 1: "Martes", 2: "Miércoles",
    3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo",
}

_PLATFORM_MAP: dict[str, str] = {
    "instagram": "instagram",
    "tiktok": "tiktok",
}

# Mapeo de texto libre del LLM → enum ContentFormat
_FORMAT_MAP: dict[str, ContentFormat] = {
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
    """
    Extrae el valor de un campo del bloque de texto del LLM.

    Tolera múltiples variantes de formato que Qwen/Mistral producen:
      **CAMPO**: valor
      *CAMPO*: valor
      CAMPO: valor
      CAMPO:: valor
      * **CAMPO**: valor
    """
    m = re.search(
        rf"(?:\*{{0,2}}){re.escape(name)}(?:\*{{0,2}})\s*[_:]{{1,2}}\*?\s*(.+?)"
        rf"(?=\n\s*[\*\-]?\s*(?:\*{{0,2}})[A-ZÁÉÍÓÚÑ]{{2,}}(?:\*{{0,2}})\s*[_:]{{1,2}}\*?|\Z)",
        block,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None
    val = m.group(1).strip()
    val = re.sub(r"^[\*\-\s\"]+|[\*\s\"]+$", "", val).strip()
    return val if val else None


_DAY_PATTERN = r"Lunes|Mart[eé]s|Mi[eé]rcoles|Jueves|Viernes|S[aá]bado|Domingo"


def _split_into_post_blocks(text: str) -> list[str]:
    """
    Divide la respuesta del LLM en bloques individuales por publicación.

    Estrategia principal: separar por delimitadores `---`.
    Estrategia de respaldo: si un bloque contiene múltiples días, lo re-divide
    por nombre de día (el LLM a veces omite los `---`).
    """
    # Split primario por --- (formato que pedimos en el prompt)
    rough_blocks = re.split(r"(?m)^\s*-{3,}\s*$", text)

    blocks = []
    for block in rough_blocks:
        day_hits = list(re.finditer(
            rf"(?:^|\n)\s*[\*\#]{{0,3}}\s*(?:{_DAY_PATTERN})\b",
            block,
            re.IGNORECASE,
        ))
        if len(day_hits) <= 1:
            blocks.append(block)
        else:
            # El LLM metió más de una publicación en un solo bloque → re-dividir
            sub_blocks = re.split(
                rf"(?=(?:^|\n)\s*[\*\#]{{0,3}}\s*(?:{_DAY_PATTERN})\b)",
                block,
                flags=re.IGNORECASE,
            )
            blocks.extend(sub_blocks)

    return blocks


def _parse_calendar_blocks(ai_response: str, week_start: date) -> list[dict]:
    """
    Convierte el texto del LLM en una lista de dicts listos para ContentPiece.

    Si un bloque no tiene día o no tiene tema/caption, se descarta silenciosamente
    y se registra en el log para detectar degradación del parser.
    """
    pieces = []
    blocks = _split_into_post_blocks(ai_response)
    discarded = 0

    for block in blocks:
        block = block.strip()
        if not block or len(block) < 30:
            continue

        # Buscar el día de la semana (con soporte para tildes y typos comunes)
        day_match = re.search(
            r"\b(Lunes|Mart[eé]s|Mi[eé]rcoles|Jueves|Viernes|S[aá]bado|Domingo)\b",
            block, re.IGNORECASE,
        )
        if not day_match:
            discarded += 1
            continue

        day_raw = day_match.group(1).lower()
        day_offset = _DAY_NAME_TO_OFFSET.get(day_raw)
        if day_offset is None:
            discarded += 1
            continue

        # Determinar plataforma; si es ambiguo, inferir por el formato
        plat_match = re.search(r"\b(Instagram|TikTok)\b", block, re.IGNORECASE)
        if plat_match:
            platform = plat_match.group(1).lower()
        elif re.search(r"\b(Reel|Carrusel|Story|Stories)\b", block, re.IGNORECASE):
            platform = "instagram"
        else:
            platform = "instagram"  # default conservador

        # Formato de contenido
        fmt_match = re.search(
            r"\b(Reel|Reels|Carrusel|Carousel|Imagen|Foto|Story|Stories|Historia|Video|Live|Directo)\b",
            block, re.IGNORECASE,
        )
        format_raw = fmt_match.group(1).lower() if fmt_match else "imagen"
        content_format = _FORMAT_MAP.get(format_raw, ContentFormat.SINGLE_IMAGE)

        # Hora programada — opcional, no bloquea si el LLM no la incluye
        hora_str = _extract_field(block, "HORA")
        scheduled_time = None
        if hora_str:
            t_match = re.search(r"(\d{1,2}:\d{2})", hora_str)
            if t_match:
                try:
                    scheduled_time = time.fromisoformat(t_match.group(1))
                except ValueError:
                    pass

        # Extraer hashtags como lista (el LLM los escribe con #)
        hashtags_raw = _extract_field(block, "HASHTAGS")
        hashtags = re.findall(r"#\w+", hashtags_raw) if hashtags_raw else []

        topic = (_extract_field(block, "TEMA") or "")[:500]
        caption = _extract_field(block, "CAPTION") or ""
        hook = (_extract_field(block, "GANCHO") or "")[:500]
        visual = _extract_field(block, "VISUAL")
        cta = (_extract_field(block, "CTA") or "")[:500]

        # Si no hay tema ni caption, el bloque no tiene contenido útil
        if not topic and not caption:
            discarded += 1
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

    if discarded:
        logger.warning("Parser de calendario: %d bloques descartados de %d totales", discarded, len(blocks))

    return pieces


async def _save_calendar_from_response(
    db: AsyncSession,
    conversation: Conversation,
    ai_response: str,
) -> None:
    """
    Crea un ContentCalendar + ContentPieces a partir de la respuesta del LLM.

    El calendario siempre empieza el próximo lunes desde hoy.
    Si el parsing devuelve 0 piezas, igual se crea el calendario (vacío)
    para que el usuario pueda editarlo manualmente desde la UI.
    """
    try:
        today = date.today()
        # Calcular el próximo lunes (si hoy es lunes, ir al siguiente)
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        week_start = today + timedelta(days=days_until_monday)
        week_end = week_start + timedelta(days=6)

        # Usar la primera línea no vacía como resumen de la estrategia
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
        db.add(UserActivity(
            user_id=conversation.user_id,
            event_type="calendar_created",
            metadata_={
                "calendar_id": str(calendar.id),
                "business_id": str(conversation.business_id),
            },
        ))
        await db.flush()

        parsed_pieces = _parse_calendar_blocks(ai_response, week_start)
        for piece_data in parsed_pieces:
            db.add(ContentPiece(calendar_id=calendar.id, **piece_data))

        await db.flush()
        logger.info(
            "Calendario creado: %s | %d publicaciones parseadas",
            calendar.id, len(parsed_pieces),
        )

    except Exception as e:
        # No propagamos el error — el usuario ya recibió la respuesta del LLM.
        # El calendario simplemente no se crea; puede intentarlo de nuevo.
        logger.error("Error al guardar calendario: %s", e, exc_info=True)
