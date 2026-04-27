"""
Admin Service — Gestión de usuarios y auditoría de actividad.

Solo accesible por usuarios con role='admin' (verificado en deps.py).

Operaciones disponibles:
  - Listar usuarios con paginación y filtros
  - Ver detalle completo de un usuario (contadores, último login)
  - Desactivar cuenta (soft delete): bloquea el login, conserva datos
  - Reactivar cuenta
  - Eliminar cuenta (hard delete): irreversible, borra todo via CASCADE
  - Listar log de actividad global con filtros

Nota sobre el hard delete:
  Usamos SQL directo en lugar del ORM para evitar que SQLAlchemy intente
  hacer SET user_id=NULL en subscriptions (viola el NOT NULL constraint).
  El CASCADE de la FK en Postgres borra todo lo relacionado automáticamente.
"""
from datetime import datetime
from math import ceil
from uuid import UUID

from sqlalchemy import delete as sql_delete, func, select, text, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.content_calendar import ContentCalendar
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.models.user_activity import UserActivity
from app.schemas.admin import (
    ActivityItem,
    ActivityListResponse,
    AdminActionResponse,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
)


# ── Listado de usuarios ───────────────────────────────────────────────────────

async def list_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    email_filter: str | None = None,
    role_filter: str | None = None,
    is_active_filter: bool | None = None,
) -> AdminUserListResponse:
    """
    Lista usuarios con paginación y filtros opcionales.

    Optimización N+1:
      En lugar de hacer 3 queries por usuario (conversaciones, mensajes, último login),
      usamos 3 queries con GROUP BY que traen los contadores de TODOS los usuarios
      de la página de una sola vez. Con 20 usuarios: 3 queries en vez de 60.
    """
    base_q = select(User)

    if email_filter:
        base_q = base_q.where(User.email.ilike(f"%{email_filter}%"))
    if role_filter:
        base_q = base_q.where(User.role == role_filter)
    if is_active_filter is not None:
        base_q = base_q.where(User.is_active == is_active_filter)

    # Total para la paginación
    total: int = (await db.execute(
        select(func.count()).select_from(base_q.subquery())
    )).scalar_one()

    # Página actual
    offset = (page - 1) * page_size
    users = (await db.execute(
        base_q.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )).scalars().all()

    if not users:
        return AdminUserListResponse(
            items=[], total=total, page=page,
            page_size=page_size, total_pages=ceil(total / page_size) if total else 1,
        )

    user_ids = [u.id for u in users]

    # ── Query 1: conversaciones por usuario (GROUP BY en vez de N queries) ──
    conv_rows = (await db.execute(
        select(Conversation.user_id, func.count().label("cnt"))
        .where(Conversation.user_id.in_(user_ids))
        .group_by(Conversation.user_id)
    )).all()
    conv_counts = {row.user_id: row.cnt for row in conv_rows}

    # ── Query 2: mensajes por usuario (JOIN + GROUP BY) ─────────────────────
    msg_rows = (await db.execute(
        select(Conversation.user_id, func.count(Message.id).label("cnt"))
        .join(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id.in_(user_ids))
        .group_by(Conversation.user_id)
    )).all()
    msg_counts = {row.user_id: row.cnt for row in msg_rows}

    # ── Query 3: último login por usuario (subquery con DISTINCT ON) ────────
    # Para cada usuario obtenemos el created_at del evento "login" más reciente.
    login_rows = (await db.execute(
        select(UserActivity.user_id, func.max(UserActivity.created_at).label("last"))
        .where(
            UserActivity.user_id.in_(user_ids),
            UserActivity.event_type == "login",
        )
        .group_by(UserActivity.user_id)
    )).all()
    last_logins = {row.user_id: row.last for row in login_rows}

    items = [
        AdminUserListItem(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            is_verified=u.is_verified,
            created_at=u.created_at,
            total_conversations=conv_counts.get(u.id, 0),
            total_messages=msg_counts.get(u.id, 0),
            last_login_at=last_logins.get(u.id),
        )
        for u in users
    ]

    return AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 1,
    )


async def get_user_detail(db: AsyncSession, user_id: UUID) -> AdminUserDetail | None:
    """Detalle completo de un usuario con todos sus contadores."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return None

    conv_count: int = (await db.execute(
        select(func.count()).where(Conversation.user_id == user.id)
    )).scalar_one()

    msg_count: int = (await db.execute(
        select(func.count())
        .select_from(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user.id)
    )).scalar_one()

    biz_count: int = (await db.execute(
        select(func.count()).where(Business.owner_id == user.id)
    )).scalar_one()

    cal_count: int = (await db.execute(
        select(func.count())
        .select_from(ContentCalendar)
        .join(Conversation, ContentCalendar.conversation_id == Conversation.id)
        .where(Conversation.user_id == user.id)
    )).scalar_one()

    last_login = (await db.execute(
        select(func.max(UserActivity.created_at))
        .where(
            UserActivity.user_id == user.id,
            UserActivity.event_type == "login",
        )
    )).scalar_one_or_none()

    return AdminUserDetail(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        total_conversations=conv_count,
        total_messages=msg_count,
        last_login_at=last_login,
        businesses_count=biz_count,
        calendars_count=cal_count,
    )


# ── Acciones sobre usuarios ───────────────────────────────────────────────────

async def deactivate_user(db: AsyncSession, user_id: UUID) -> AdminActionResponse:
    """
    Soft delete: pone is_active=False.

    El usuario sigue en DB con todos sus datos intactos.
    No puede iniciar sesión (verificado en login_user y refresh_access_token).
    """
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()

    if not user:
        return AdminActionResponse(ok=False, message="Usuario no encontrado")
    if not user.is_active:
        return AdminActionResponse(ok=False, message="El usuario ya está desactivado")

    user.is_active = False
    await db.commit()
    return AdminActionResponse(ok=True, message=f"Usuario {user.email} desactivado")


async def reactivate_user(db: AsyncSession, user_id: UUID) -> AdminActionResponse:
    """Reactiva una cuenta previamente desactivada."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()

    if not user:
        return AdminActionResponse(ok=False, message="Usuario no encontrado")

    user.is_active = True
    await db.commit()
    return AdminActionResponse(ok=True, message=f"Usuario {user.email} reactivado")


async def delete_user_hard(db: AsyncSession, user_id: UUID) -> AdminActionResponse:
    """
    Hard delete: elimina definitivamente al usuario y TODA su información.

    Usamos SQL directo porque el ORM de SQLAlchemy, al hacer DELETE en User,
    intenta hacer SET user_id=NULL en subscriptions antes de borrar el registro,
    violando el NOT NULL constraint. Con SQL directo borramos primero las
    subscriptions y luego el usuario — el CASCADE de Postgres elimina el resto.

    Datos eliminados en cascada: businesses, conversations, messages,
    content_calendars, content_pieces, documents, rag_chunks, user_activities.

    ADVERTENCIA: Esta operación es irreversible.
    """
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        return AdminActionResponse(ok=False, message="Usuario no encontrado")

    email = user.email

    # Borrar suscripciones primero (también limpia posibles registros corruptos
    # con user_id=NULL que bloquearían el DELETE del usuario)
    await db.execute(
        text("DELETE FROM subscriptions WHERE user_id = :uid OR user_id IS NULL"),
        {"uid": str(user_id)},
    )
    # El CASCADE en la FK borra businesses, conversations, messages, etc.
    await db.execute(
        text("DELETE FROM users WHERE id = :uid"),
        {"uid": str(user_id)},
    )
    await db.commit()
    return AdminActionResponse(ok=True, message=f"Usuario {email} eliminado permanentemente")


# ── Log de actividad global ───────────────────────────────────────────────────

async def list_activity(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    user_id_filter: UUID | None = None,
    event_type_filter: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> ActivityListResponse:
    """Lista el log de actividad global con filtros opcionales y paginación."""
    base_q = select(UserActivity, User.email).join(User, UserActivity.user_id == User.id)

    if user_id_filter:
        base_q = base_q.where(UserActivity.user_id == user_id_filter)
    if event_type_filter:
        base_q = base_q.where(UserActivity.event_type == event_type_filter)
    if date_from:
        base_q = base_q.where(UserActivity.created_at >= date_from)
    if date_to:
        base_q = base_q.where(UserActivity.created_at <= date_to)

    total: int = (await db.execute(
        select(func.count()).select_from(base_q.subquery())
    )).scalar_one()

    offset = (page - 1) * page_size
    rows = (await db.execute(
        base_q.order_by(UserActivity.created_at.desc()).offset(offset).limit(page_size)
    )).all()

    items = [
        ActivityItem(
            id=activity.id,
            user_id=activity.user_id,
            user_email=email,
            event_type=activity.event_type,
            metadata_=activity.metadata_,
            created_at=activity.created_at,
        )
        for activity, email in rows
    ]

    return ActivityListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 1,
    )
