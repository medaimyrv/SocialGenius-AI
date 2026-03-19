"""
RAG Service — Retrieval Augmented Generation.

Embeddings: fastembed (ONNX BAAI/bge-small-en-v1.5, 384 dims, sin torch)
Vector store: tabla rag_chunks en Postgres/SQLite
Búsqueda: similitud coseno calculada en Python (sin pgvector)

Fuentes indexadas:
  - "document" → chunks de PDFs/TXTs subidos por el usuario
  - "message"  → mensajes del historial de conversaciones
"""
import logging
import math
import uuid
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rag_chunk import RagChunk

logger = logging.getLogger(__name__)

TOP_K = 5
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ── Modelo de embeddings ──────────────────────────────────────────────────────

_embedding_model = None


def _embed(texts: list[str]) -> list[list[float]]:
    """Genera embeddings con fastembed (se descarga el modelo la primera vez)."""
    global _embedding_model
    if _embedding_model is None:
        from fastembed import TextEmbedding
        _embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return [v.tolist() for v in _embedding_model.embed(texts)]


def _embed_one(text: str) -> list[float]:
    return _embed([text])[0]


# ── Similitud coseno ──────────────────────────────────────────────────────────

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ── Chunking ─────────────────────────────────────────────────────────────────

def _chunk_text(text_: str) -> list[str]:
    words = text_.split()
    chunks, start = [], 0
    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 20:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
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
        embeddings = _embed(chunks)
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
        embedding = _embed_one(content)
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
        query_embedding = _embed_one(query)
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
