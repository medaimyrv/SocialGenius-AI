"""fix production schema: role, brand_voice, user_activity, documents, subscriptions

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-19

Fixes:
- Agrega columna 'role' a users (faltaba en migración inicial)
- Aumenta brand_voice a Text (era varchar(100), muy corto)
- Crea tabla user_activity (faltaba en migración inicial)
- Crea tabla documents (faltaba en migración inicial)
- Limpia subscriptions con user_id = null (datos corruptos)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name

    # ── 1. Columna role en users ──────────────────────────────────────────────
    # Verificar si ya existe antes de agregar (por si se corre dos veces)
    if dialect == "postgresql":
        result = conn.execute(sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='role'"
        ))
        if not result.fetchone():
            op.add_column("users", sa.Column("role", sa.String(length=20), nullable=False, server_default="user"))
    else:
        # SQLite: batch_alter para agregar columna con default
        with op.batch_alter_table("users") as batch_op:
            try:
                batch_op.add_column(sa.Column("role", sa.String(length=20), nullable=False, server_default="user"))
            except Exception:
                pass  # Ya existe

    # ── 2. brand_voice: varchar(100) → Text ──────────────────────────────────
    if dialect == "postgresql":
        conn.execute(sa.text("ALTER TABLE businesses ALTER COLUMN brand_voice TYPE TEXT"))
    else:
        with op.batch_alter_table("businesses") as batch_op:
            batch_op.alter_column("brand_voice", type_=sa.Text())

    # ── 3. Tabla user_activity ────────────────────────────────────────────────
    if not _table_exists(conn, dialect, "user_activity"):
        op.create_table(
            "user_activity",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("event_type", sa.String(length=100), nullable=False),
            sa.Column("metadata_", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_user_activity_user_id", "user_activity", ["user_id"])
        op.create_index("ix_user_activity_event_type", "user_activity", ["event_type"])

    # ── 4. Tabla documents ────────────────────────────────────────────────────
    if not _table_exists(conn, dialect, "documents"):
        op.create_table(
            "documents",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("business_id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("content_type", sa.String(length=100), nullable=False),
            sa.Column("text_content", sa.Text(), nullable=False),
            sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
            sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_documents_business_id", "documents", ["business_id"])

    # ── 5. Limpiar subscriptions con user_id = null (datos corruptos) ─────────
    conn.execute(sa.text("DELETE FROM subscriptions WHERE user_id IS NULL"))


def downgrade() -> None:
    # No revertimos la limpieza de datos corruptos
    pass


def _table_exists(conn, dialect: str, table_name: str) -> bool:
    """Verifica si una tabla existe en la base de datos."""
    if dialect == "postgresql":
        result = conn.execute(sa.text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname='public' AND tablename=:t"
        ), {"t": table_name})
    else:
        result = conn.execute(sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:t"
        ), {"t": table_name})
    return result.fetchone() is not None
