"""add pgvector and rag_chunks table

Revision ID: a1b2c3d4e5f6
Revises: bc70a3e09f0d
Create Date: 2026-03-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "bc70a3e09f0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        # Activar extensión pgvector (viene instalada en Railway por defecto)
        conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    # Columna de embedding: vector(384) en Postgres, TEXT en SQLite
    if dialect == "postgresql":
        from pgvector.sqlalchemy import Vector
        embedding_col = sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True)
    else:
        embedding_col = sa.Column("embedding", sa.Text(), nullable=True)

    op.create_table(
        "rag_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("business_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("role", sa.String(length=20), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        embedding_col,
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rag_chunks_business_id", "rag_chunks", ["business_id"])
    op.create_index(
        "ix_rag_chunks_business_source",
        "rag_chunks",
        ["business_id", "source_type"],
    )

    # Índice HNSW de pgvector para búsqueda por similitud coseno (solo Postgres)
    if dialect == "postgresql":
        conn.execute(sa.text(
            "CREATE INDEX ix_rag_chunks_embedding_hnsw "
            "ON rag_chunks USING hnsw (embedding vector_cosine_ops)"
        ))


def downgrade() -> None:
    op.drop_table("rag_chunks")
