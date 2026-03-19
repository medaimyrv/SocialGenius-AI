"""
RAG Service — Retrieval Augmented Generation.

Embeddings: HuggingFace Inference API (intfloat/multilingual-e5-small, 384 dims)
  - Modelo multilingüe entrenado en español → mejor precisión semántica
  - Requiere prefijos obligatorios del protocolo E5:
      "passage: <texto>"  → al indexar documentos y mensajes
      "query: <texto>"    → al generar el embedding de búsqueda
Vector store: tabla rag_chunks en Postgres/SQLite
Búsqueda: similitud coseno calculada en Python (sin pgvector)
Chunking: por oraciones (respeta límites semánticos, nunca parte una frase)

Fuentes indexadas:
  - "document" → chunks de PDFs/TXTs subidos por el usuario
  - "message"  → mensajes del historial de conversaciones
"""
import logging
import math
import re
import uuid
from typing import Literal

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.rag_chunk import RagChunk

logger = logging.getLogger(__name__)

TOP_K = 5
CHUNK_MAX_WORDS = 300   # máximo de palabras por chunk (agrupando oraciones)
CHUNK_OVERLAP_SENTENCES = 2  # oraciones que se solapan entre chunks consecutivos

HF_EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_EMBEDDING_MODEL}"

# ── Embeddings vía HuggingFace Inference API ──────────────────────────────────
# multilingual-e5 exige prefijos para distinguir rol semántico:
#   "passage: <texto>"  → contenido a indexar (documentos, mensajes)
#   "query: <texto>"    → consulta de búsqueda del usuario

async def _embed(texts: list[str], is_query: bool = False) -> list[list[float]]:
    """
    Genera embeddings con multilingual-e5-small.
    is_query=True  → prefija con "query: "   (para búsquedas)
    is_query=False → prefija con "passage: " (para indexar contenido)
    """
    prefix = "query: " if is_query else "passage: "
    prefixed = [prefix + t for t in texts]
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(HF_API_URL, headers=headers, json={"inputs": prefixed})
        resp.raise_for_status()
        result = resp.json()
    return result


async def _embed_passages(texts: list[str]) -> list[list[float]]:
    """Embeddings para contenido a indexar (documentos, mensajes)."""
    return await _embed(texts, is_query=False)


async def _embed_query(text: str) -> list[float]:
    """Embedding para una consulta de búsqueda."""
    return (await _embed([text], is_query=True))[0]


# ── Similitud coseno ──────────────────────────────────────────────────────────

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ── Chunking por oraciones ────────────────────────────────────────────────────

def _split_sentences(text_: str) -> list[str]:
    """
    Divide el texto en oraciones respetando límites naturales del lenguaje.
    Maneja puntos en abreviaturas, números decimales y puntos suspensivos.
    """
    # Normalizar saltos de línea múltiples como separadores de párrafo
    text_ = re.sub(r"\n{2,}", " <PARA> ", text_)
    text_ = re.sub(r"\n", " ", text_)

    # Separar en oraciones: punto/exclamación/interrogación seguido de espacio y mayúscula
    # Excluye: números decimales (3.5), abreviaturas cortas (Sr., Dr.)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ\"])|(?<=<PARA>)\s*", text_)

    result = []
    for s in sentences:
        s = s.replace("<PARA>", "").strip()
        if len(s) > 15:  # ignorar fragmentos muy cortos
            result.append(s)
    return result


def _chunk_text(text_: str) -> list[str]:
    """
    Agrupa oraciones en chunks sin superar CHUNK_MAX_WORDS palabras.
    El solapamiento se hace a nivel de oración (CHUNK_OVERLAP_SENTENCES),
    preservando siempre el contexto semántico completo.
    """
    sentences = _split_sentences(text_)
    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        word_count = len(sentence.split())

        if current_words + word_count > CHUNK_MAX_WORDS and current:
            # Guardar chunk actual
            chunks.append(" ".join(current))
            # Overlap: conservar las últimas N oraciones para el siguiente chunk
            overlap = current[-CHUNK_OVERLAP_SENTENCES:]
            current = overlap
            current_words = sum(len(s.split()) for s in current)
        else:
            current.append(sentence)
            current_words += word_count
            i += 1

    if current:
        chunks.append(" ".join(current))

    return chunks


# ── Indexado ──────────────────────────────────────────────────────────────────

async def index_document(
    db: AsyncSession,
    business_id: str,
    document_id: str,
    filename: str,
    text_: str,
) -> int:
    """Divide el documento en chunks, genera embeddings y los guarda. Retorna nº de chunks."""
    chunks = _chunk_text(text_)
    if not chunks:
        return 0
    try:
        embeddings = await _embed_passages(chunks)
        rows = [
            RagChunk(
                id=uuid.uuid4(),
                business_id=uuid.UUID(business_id),
                source_type="document",
                source_id=document_id,
                filename=filename,
                chunk_index=i,
                content=chunk,
                embedding=emb,
            )
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        db.add_all(rows)
        await db.flush()
        return len(rows)
    except Exception as e:
        logger.error(f"Error indexing document {document_id}: {e}")
        return 0


async def index_message(
    db: AsyncSession,
    business_id: str,
    conversation_id: str,
    role: Literal["user", "assistant"],
    content: str,
) -> None:
    """Indexa un mensaje para recuperación futura."""
    try:
        embedding = (await _embed_passages([content]))[0]
        db.add(RagChunk(
            id=uuid.uuid4(),
            business_id=uuid.UUID(business_id),
            source_type="message",
            source_id=conversation_id,
            role=role,
            chunk_index=0,
            content=content,
            embedding=embedding,
        ))
        await db.flush()
    except Exception as e:
        logger.error(f"Error indexing message: {e}")


async def delete_document_chunks(
    db: AsyncSession,
    business_id: str,
    document_id: str,
) -> None:
    """Elimina todos los chunks de un documento."""
    await db.execute(
        delete(RagChunk).where(
            RagChunk.business_id == uuid.UUID(business_id),
            RagChunk.source_type == "document",
            RagChunk.source_id == document_id,
        )
    )
    await db.flush()


# ── Recuperación ──────────────────────────────────────────────────────────────

async def retrieve_context(
    db: AsyncSession,
    business_id: str,
    query: str,
) -> str:
    """
    Recupera los chunks más relevantes (documentos + mensajes) para el query.
    Retorna texto formateado listo para inyectar en el prompt de la IA.
    """
    try:
        query_embedding = await _embed_query(query)
    except Exception as e:
        logger.warning(f"Error generating query embedding: {e}")
        return ""

    bid = uuid.UUID(business_id)
    doc_chunks = await _search(db, bid, query_embedding, "document")
    msg_chunks = await _search(db, bid, query_embedding, "message")

    parts = []
    if msg_chunks:
        lines = [
            f"{'Usuario' if c.role == 'user' else 'Asistente'}: {c.content}"
            for c in msg_chunks
        ]
        parts.append("### Conversaciones anteriores relevantes:\n" + "\n".join(lines))

    if doc_chunks:
        lines = [f"[{c.filename or 'documento'}]: {c.content}" for c in doc_chunks]
        parts.append("### Documentos de referencia:\n" + "\n".join(lines))

    return "\n\n".join(parts)


async def _search(
    db: AsyncSession,
    business_id: uuid.UUID,
    query_embedding: list[float],
    source_type: str,
) -> list[RagChunk]:
    """Carga chunks del negocio y retorna los TOP_K más similares al query."""
    chunks = (await db.execute(
        select(RagChunk).where(
            RagChunk.business_id == business_id,
            RagChunk.source_type == source_type,
            RagChunk.embedding.isnot(None),
        )
    )).scalars().all()

    if not chunks:
        return []

    scored = sorted(
        [(c, _cosine_similarity(query_embedding, c.embedding)) for c in chunks if c.embedding],
        key=lambda x: x[1],
        reverse=True,
    )
    return [c for c, _ in scored[:TOP_K]]
