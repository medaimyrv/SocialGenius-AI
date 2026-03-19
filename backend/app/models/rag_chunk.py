"""
Modelo RagChunk — almacena chunks de texto con embeddings vectoriales.

Embeddings guardados como:
- JSONB en PostgreSQL (Postgres nativo, consultas eficientes)
- TEXT (JSON) en SQLite (desarrollo local)

La búsqueda por similitud coseno se hace siempre en Python.
"""
import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator
import json

from app.models.base import Base, TimestampMixin, UUIDMixin

EMBEDDING_DIM = 384  # BAAI/bge-small-en-v1.5


class EmbeddingType(TypeDecorator):
    """
    Guarda embeddings como JSONB en Postgres o TEXT en SQLite.
    Transparente para el resto del código: acepta y devuelve list[float].
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            # JSONB acepta lista Python directamente
            return value if isinstance(value, list) else list(value)
        # SQLite: serializar como JSON string
        if hasattr(value, "tolist"):
            value = value.tolist()
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value  # JSONB ya devuelve lista
        if isinstance(value, str):
            return json.loads(value)
        return value


class RagChunk(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "rag_chunks"

    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "document" | "message"
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # document_id o conversation_id según source_type
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # Metadatos extra según fuente
    filename: Mapped[str | None] = mapped_column(String(255))
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    role: Mapped[str | None] = mapped_column(String(20))  # "user" | "assistant"
    # Contenido textual del chunk
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Vector de embedding (lista de floats)
    embedding: Mapped[list | None] = mapped_column(EmbeddingType, nullable=True)

    __table_args__ = (
        Index("ix_rag_chunks_business_source", "business_id", "source_type"),
    )
