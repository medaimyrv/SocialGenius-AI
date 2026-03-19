"""
Modelo RagChunk — almacena chunks de texto con embeddings vectoriales.

Compatible con:
- PostgreSQL + pgvector (producción / Railway): columna nativa Vector(384)
- SQLite (desarrollo local): embedding guardado como JSON text

Fuentes:
- source_type="document" → chunks de PDFs/TXTs subidos por el usuario
- source_type="message"  → mensajes del historial de conversaciones
"""
import json
import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.models.base import Base, TimestampMixin, UUIDMixin

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class VectorType(TypeDecorator):
    """
    TypeDecorator que usa pgvector.Vector en PostgreSQL y Text (JSON) en SQLite.
    Transparente para el resto del código.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector
            return dialect.type_descriptor(Vector(EMBEDDING_DIM))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            # pgvector acepta lista de floats directamente
            if hasattr(value, "tolist"):
                return value.tolist()
            return value
        # SQLite: serializar como JSON
        if hasattr(value, "tolist"):
            value = value.tolist()
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            # pgvector devuelve lista de floats directamente
            return list(value) if not isinstance(value, list) else value
        # SQLite: deserializar JSON
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
    # Vector de embedding (384 dims)
    embedding: Mapped[list | None] = mapped_column(VectorType, nullable=True)

    __table_args__ = (
        # Índice para filtrar por negocio + tipo de fuente
        Index("ix_rag_chunks_business_source", "business_id", "source_type"),
    )
