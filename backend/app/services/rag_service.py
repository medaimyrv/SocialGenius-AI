"""
RAG Service — Retrieval Augmented Generation con pgvector.

Embeddings: fastembed (ONNX MiniLM-L6-v2, 384 dims, sin torch)
Vector store:
  - PostgreSQL (Railway): columna nativa vector(384) + índice HNSW, búsqueda SQL con <=>
  - SQLite (desarrollo local): embeddings como JSON, similitud coseno en Python

Fuentes indexadas:
  - "document" → chunks de PDFs/TXTs subidos por el usuario
  - "message"  → mensajes del historial de conversaciones
"""
import json
import logging
import math
import uuid
from typing import Literal

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rag_chunk import RagChunk

logger = logging.getLogger(__name__)

TOP_K = 5
EMBEDDING_DIM = 384
CHUNK_SIZE = 500   # palabras por chunk
CHUNK_OVERLAP = 50  # palabras de overlap entre chunks


# ── Modelo de embeddings ──────────────────────────────────────────────────────

def _get_embedding_model():
    """Carga el modelo fastembed (singleton, se descarga una vez)."""
    from fastembed import TextEmbedding
    return TextEmbedding(model_name="BAAI/bge-small-en-v1.5")  # 384 dims, muy ligero


_embedding_model = None


def _embed(texts: list[str]) -> list[list[float]]:
    """Genera embeddings para una lista de textos. Retorna lista de vectores."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = _get_embedding_model()
    return [v.tolist() for v in _embedding_model.embed(texts)]


def _embed_one(text: str) -> list[float]:
    return _embed([text])[0]


# ── Similitud coseno (solo para SQLite) ──────────────────────────────────────

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ── Helpers internos ─────────────────────────────────────────────────────────

def _is_postgres(db: AsyncSession) -> bool:
    return db.get_bind().dialect.name == "postgresql"


def _chunk_text(text_: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto en chunks de palabras con overlap."""
    words = text_.split()
    chunks, start = [], 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) > 20:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ── Indexado ──────────────────────────────────────────────────────────────────

async def index_document(
    db: AsyncSession,
    business_id: str,
    document_id: str,
    filename: str,
    text_: str,
) -> int:
    """
    Divide el documento en chunks, genera embeddings y los guarda en rag_chunks.
    Retorna la cantidad de chunks indexados.
    """
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
    """Indexa un mensaje en rag_chunks para recuperación futura."""
    try:
        embedding = _embed_one(content)
        chunk = RagChunk(
            id=uuid.uuid4(),
            business_id=uuid.UUID(business_id),
            source_type="message",
            source_id=conversation_id,
            role=role,
            chunk_index=0,
            content=content,
            embedding=embedding,
        )
        db.add(chunk)
        await db.flush()
    except Exception as e:
        logger.error(f"Error indexing message: {e}")


async def delete_document_chunks(
    db: AsyncSession,
    business_id: str,
    document_id: str,
) -> None:
    """Elimina todos los chunks de un documento del vector store."""
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
    query_embedding = _embed_one(query)
    bid = uuid.UUID(business_id)

    doc_chunks = await _search(db, bid, query_embedding, source_type="document")
    msg_chunks = await _search(db, bid, query_embedding, source_type="message")

    parts = []
    if msg_chunks:
        lines = []
        for chunk in msg_chunks:
            label = "Usuario" if chunk.role == "user" else "Asistente"
            lines.append(f"{label}: {chunk.content}")
        parts.append("### Conversaciones anteriores relevantes:\n" + "\n".join(lines))

    if doc_chunks:
        lines = []
        for chunk in doc_chunks:
            fname = chunk.filename or "documento"
            lines.append(f"[{fname}]: {chunk.content}")
        parts.append("### Documentos de referencia:\n" + "\n".join(lines))

    return "\n\n".join(parts)


async def _search(
    db: AsyncSession,
    business_id: uuid.UUID,
    query_embedding: list[float],
    source_type: str,
) -> list[RagChunk]:
    """
    Busca los TOP_K chunks más similares al query.
    - PostgreSQL: usa el operador <=> de pgvector (búsqueda ANN en el índice HNSW)
    - SQLite: carga todos los chunks del negocio y calcula similitud en Python
    """
    try:
        bind = db.get_bind()
        dialect = bind.dialect.name
    except Exception:
        dialect = "sqlite"

    if dialect == "postgresql":
        return await _search_postgres(db, business_id, query_embedding, source_type)
    return await _search_sqlite(db, business_id, query_embedding, source_type)


async def _search_postgres(
    db: AsyncSession,
    business_id: uuid.UUID,
    query_embedding: list[float],
    source_type: str,
) -> list[RagChunk]:
    """Búsqueda por similitud coseno con pgvector (<=>)."""
    from pgvector.sqlalchemy import Vector

    vec_literal = f"'[{','.join(str(x) for x in query_embedding)}]'::vector"

    result = await db.execute(
        text(
            f"""
            SELECT id FROM rag_chunks
            WHERE business_id = :business_id AND source_type = :source_type
            ORDER BY embedding <=> {vec_literal}
            LIMIT :limit
            """
        ),
        {"business_id": str(business_id), "source_type": source_type, "limit": TOP_K},
    )
    ids = [row[0] for row in result.fetchall()]
    if not ids:
        return []

    chunks = (await db.execute(
        select(RagChunk).where(RagChunk.id.in_(ids))
    )).scalars().all()
    return list(chunks)


async def _search_sqlite(
    db: AsyncSession,
    business_id: uuid.UUID,
    query_embedding: list[float],
    source_type: str,
) -> list[RagChunk]:
    """Búsqueda por similitud coseno en Python (SQLite local)."""
    chunks = (await db.execute(
        select(RagChunk).where(
            RagChunk.business_id == business_id,
            RagChunk.source_type == source_type,
            RagChunk.embedding.isnot(None),
        )
    )).scalars().all()

    if not chunks:
        return []

    scored = [
        (chunk, _cosine_similarity(query_embedding, chunk.embedding))
        for chunk in chunks
        if chunk.embedding
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in scored[:TOP_K]]
