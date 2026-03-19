"""add rag_chunks table (sin pgvector, embeddings como JSON)

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


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # Embeddings: JSONB en Postgres, TEXT en SQLite
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import JSONB
        embedding_col = sa.Column("embedding", JSONB(), nullable=True)
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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rag_chunks_business_id", "rag_chunks", ["business_id"])
    op.create_index("ix_rag_chunks_business_source", "rag_chunks", ["business_id", "source_type"])


def downgrade() -> None:
    op.drop_table("rag_chunks")
