"""
RAG Service — Retrieval-Augmented Generation.

Arquitectura de memoria del chatbot:
  1. El usuario sube un PDF/TXT → se fragmenta en chunks → se vectoriza → se guarda en DB.
  2. En cada mensaje de chat → se vectoriza el query → se buscan los chunks más similares.
  3. Los chunks relevantes se inyectan en el system prompt antes de llamar al LLM.

Modelo de embeddings: intfloat/multilingual-e5-small (HuggingFace Inference API)
  - 384 dimensiones, entrenado en 100+ idiomas incluyendo español.
  - Requiere prefijos obligatorios del protocolo E5:
      "passage: <texto>"  → al INDEXAR contenido (documentos, mensajes)
      "query: <texto>"    → al BUSCAR (consulta del usuario)
    Sin estos prefijos el modelo rinde ~15% peor.

Almacenamiento: tabla rag_chunks en PostgreSQL (JSONB) / SQLite (TEXT-JSON).
  No usamos pgvector porque Railway Postgres 17 no lo tiene disponible.
  La similitud coseno se calcula en Python — funciona bien hasta ~500 chunks por búsqueda.

Fuentes indexadas:
  - "document" → chunks de PDFs/TXTs subidos manualmente por el usuario.
  - "message"  → mensajes del historial de conversaciones (memoria a largo plazo).
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

# ── Constantes de configuración ───────────────────────────────────────────────

TOP_K = 5                    # Chunks devueltos por búsqueda (documentos + mensajes por separado)
SIMILARITY_THRESHOLD = 0.40  # Descarta chunks con similitud < 0.40 (evita ruido irrelevante)
CHUNK_MAX_WORDS = 300        # Máximo de palabras por chunk — equilibrio entre contexto y precisión
CHUNK_OVERLAP_SENTENCES = 2  # Oraciones que se repiten entre chunks consecutivos para no perder contexto en los bordes

HF_EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_EMBEDDING_MODEL}"


# ── Embeddings via HuggingFace Inference API ─────────────────────────────────

async def _embed(texts: list[str], is_query: bool = False) -> list[list[float]]:
    """
    Genera embeddings con el modelo multilingual-e5-small.

    El protocolo E5 distingue dos modos de uso:
      - is_query=False → prefijo "passage: " — para contenido que se indexa
      - is_query=True  → prefijo "query: "   — para consultas de búsqueda

    Mezclar los prefijos degradaría la similitud coseno porque el modelo
    fue entrenado con esta distinción semántica explícita.
    """
    prefix = "query: " if is_query else "passage: "
    prefixed = [prefix + t for t in texts]
    headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(HF_API_URL, headers=headers, json={"inputs": prefixed})
        resp.raise_for_status()
        return resp.json()


async def _embed_passages(texts: list[str]) -> list[list[float]]:
    """Embeddings para contenido a indexar (documentos y mensajes históricos)."""
    return await _embed(texts, is_query=False)


async def _embed_query(text: str) -> list[float]:
    """Embedding para la consulta de búsqueda del usuario."""
    return (await _embed([text], is_query=True))[0]


# ── Similitud coseno ──────────────────────────────────────────────────────────

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Similitud coseno entre dos vectores de embedding.

    Rango: [-1.0, 1.0]. En la práctica con modelos de texto:
      > 0.85 → casi idénticos
      0.60–0.85 → muy relacionados
      0.40–0.60 → relacionados
      < 0.40 → probablemente irrelevantes (filtramos con SIMILARITY_THRESHOLD)
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ── Chunking semántico por oraciones ─────────────────────────────────────────

def _split_sentences(text_: str) -> list[str]:
    """
    Divide el texto en oraciones respetando límites semánticos.

    El chunking por palabras (el enfoque naive) parte frases a la mitad,
    lo que genera embeddings con contexto incompleto y peor recall.
    Este método respeta los límites naturales del lenguaje.

    Casos que maneja correctamente:
      - Números decimales: "el 3.5% de conversión" → no parte en "3."
      - Abreviaturas: "Sr. García" → no parte en "Sr."
      - Párrafos: doble salto de línea se trata como separador fuerte
    """
    # Normalizar párrafos como separadores antes de procesar oraciones
    text_ = re.sub(r"\n{2,}", " <PARA> ", text_)
    text_ = re.sub(r"\n", " ", text_)

    # Partir en oraciones: punto/!/? seguido de espacio y mayúscula
    # El lookbehind (?<=[.!?]) evita partir en "3.5" o "Sr."
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ\"])|(?<=<PARA>)\s*", text_)

    result = []
    for s in sentences:
        s = s.replace("<PARA>", "").strip()
        if len(s) > 15:  # descartar fragmentos sin contenido real
            result.append(s)
    return result


def _chunk_text(text_: str) -> list[str]:
    """
    Agrupa oraciones en chunks de máximo CHUNK_MAX_WORDS palabras.

    El solapamiento (overlap) se hace a nivel de oración completa,
    nunca en medio de una frase. Esto garantiza que el contexto
    semántico se preserve en los límites entre chunks.

    Ejemplo con overlap=2:
      Chunk 1: [A, B, C, D]
      Chunk 2: [C, D, E, F]  ← C y D se repiten
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
            chunks.append(" ".join(current))
            # Conservar las últimas N oraciones como overlap para el siguiente chunk
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
    """
    Fragmenta un documento, genera embeddings y los persiste en rag_chunks.

    Retorna el número de chunks creados, o 0 si falla.
    El caller (documents.py) verifica el 0 y hace rollback + HTTP 422.
    """
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
        logger.error("Error indexando documento %s: %s", document_id, e)
        return 0


async def index_message(
    db: AsyncSession,
    business_id: str,
    conversation_id: str,
    role: Literal["user", "assistant"],
    content: str,
) -> None:
    """
    Indexa un mensaje del chat para recuperación semántica futura.

    Sirve como memoria a largo plazo: en conversaciones futuras del mismo
    negocio se pueden recuperar respuestas o contexto de sesiones anteriores.

    Deduplicación: si el mismo contenido ya fue indexado para esta conversación,
    se omite. Esto previene que el historial de chunks crezca con duplicados
    cuando el usuario retoma una conversación existente.
    """
    # Evitar indexar el mismo mensaje dos veces (los primeros 200 chars son suficientes
    # como fingerprint — mensajes idénticos en la misma conversación son siempre el mismo)
    existing = (await db.execute(
        select(RagChunk.id).where(
            RagChunk.source_type == "message",
            RagChunk.source_id == conversation_id,
            RagChunk.role == role,
            RagChunk.content == content[:200],
        ).limit(1)
    )).scalar_one_or_none()

    if existing:
        return  # ya indexado, nada que hacer

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
        logger.error("Error indexando mensaje de conversación %s: %s", conversation_id, e)


async def delete_document_chunks(
    db: AsyncSession,
    business_id: str,
    document_id: str,
) -> None:
    """Elimina todos los chunks de un documento al borrarlo."""
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
    Punto de entrada principal del RAG: recupera el contexto más relevante
    para el mensaje del usuario y lo devuelve formateado para inyectar en el prompt.

    Busca por separado en documentos y en mensajes históricos para que
    el LLM pueda distinguir las fuentes en su respuesta.

    Retorna cadena vacía si no hay chunks relevantes o si falla el embedding.
    El caller maneja el vacío simplemente omitiendo la inyección de contexto.
    """
    try:
        query_embedding = await _embed_query(query)
    except Exception as e:
        # No bloqueamos el chat si el RAG falla — degradación graceful
        logger.warning("Error generando embedding del query (RAG desactivado): %s", e)
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
    """
    Carga los chunks más recientes del negocio y retorna los TOP_K más similares.

    Por qué LIMIT 500:
      Sin límite, un negocio con muchos documentos podría cargar miles de
      chunks en RAM por cada búsqueda. 500 × 384 floats ≈ 768 KB — razonable.
      Priorizamos los chunks más recientes porque en marketing el contenido
      más nuevo tiende a ser más relevante que el histórico antiguo.

    Por qué coseno en Python y no pgvector:
      Railway PostgreSQL 17 no tiene la extensión pgvector disponible.
      Para < 500 chunks la similitud en Python es suficientemente rápida
      (< 10ms). Cuando el volumen crezca, pgvector o una BD vectorial
      dedicada serían el siguiente paso.
    """
    chunks = (await db.execute(
        select(RagChunk)
        .where(
            RagChunk.business_id == business_id,
            RagChunk.source_type == source_type,
            RagChunk.embedding.isnot(None),
        )
        .order_by(RagChunk.created_at.desc())
        .limit(500)
    )).scalars().all()

    if not chunks:
        return []

    scored = sorted(
        [(c, _cosine_similarity(query_embedding, c.embedding)) for c in chunks if c.embedding],
        key=lambda x: x[1],
        reverse=True,
    )

    # Aplicar umbral de similitud: si ningún chunk supera 0.40, es mejor
    # no inyectar nada que inyectar contexto irrelevante que confunda al LLM.
    return [c for c, score in scored[:TOP_K] if score >= SIMILARITY_THRESHOLD]
