"""
Servicio de administración.

Operaciones:
- Listar usuarios con paginación y filtros
- Ver detalle de usuario + contadores
- Desactivar usuario (soft delete): conserva datos, impide login
- Eliminar usuario (hard delete): borra cuenta y toda su actividad via CASCADE
- Registrar eventos de actividad
- Listar actividad global con filtros
"""
from datetime import datetime
from math import ceil
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


# ── Actividad ──────────────────────────────────────────────────────────────────

async def log_activity(
    db: AsyncSession,
    user_id: UUID,
    event_type: str,
    metadata: dict | None = None,
) -> None:
    """Registra un evento de actividad. Llámalo desde cualquier servicio."""
    activity = UserActivity(
        user_id=user_id,
        event_type=event_type,
        metadata_=metadata,
    )
    db.add(activity)
    await db.commit()


# ── Usuarios ───────────────────────────────────────────────────────────────────

async def list_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    email_filter: str | None = None,
    role_filter: str | None = None,
    is_active_filter: bool | None = None,
) -> AdminUserListResponse:
    """Lista usuarios con filtros y paginación."""
    base_q = select(User)

    if email_filter:
        base_q = base_q.where(User.email.ilike(f"%{email_filter}%"))
    if role_filter:
        base_q = base_q.where(User.role == role_filter)
    if is_active_filter is not None:
        base_q = base_q.where(User.is_active == is_active_filter)

    # Total
    count_q = select(func.count()).select_from(base_q.subquery())
    total: int = (await db.execute(count_q)).scalar_one()

    # Página
    offset = (page - 1) * page_size
    users_result = await db.execute(
        base_q.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = users_result.scalars().all()

    items = []
    for user in users:
        # Contadores
        conv_count: int = (
            await db.execute(
                select(func.count()).where(Conversation.user_id == user.id)
            )
        ).scalar_one()

        msg_count: int = (
            await db.execute(
                select(func.count())
                .select_from(Message)
                .join(Conversation, Message.conversation_id == Conversation.id)
                .where(Conversation.user_id == user.id)
            )
        ).scalar_one()

        # Último login
        last_login = (
            await db.execute(
                select(UserActivity.created_at)
                .where(
                    UserActivity.user_id == user.id,
                    UserActivity.event_type == "login",
                )
                .order_by(UserActivity.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        items.append(
            AdminUserListItem(
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
            )
        )

    return AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 1,
    )


async def get_user_detail(db: AsyncSession, user_id: UUID) -> AdminUserDetail | None:
    """Detalle completo de un usuario con todos sus contadores."""
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        return None

    conv_count: int = (
        await db.execute(select(func.count()).where(Conversation.user_id == user.id))
    ).scalar_one()

    msg_count: int = (
        await db.execute(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user.id)
        )
    ).scalar_one()

    biz_count: int = (
        await db.execute(select(func.count()).where(Business.owner_id == user.id))
    ).scalar_one()

    cal_count: int = (
        await db.execute(
            select(func.count())
            .select_from(ContentCalendar)
            .join(Conversation, ContentCalendar.conversation_id == Conversation.id)
            .where(Conversation.user_id == user.id)
        )
    ).scalar_one()

    last_login = (
        await db.execute(
            select(UserActivity.created_at)
            .where(
                UserActivity.user_id == user.id,
                UserActivity.event_type == "login",
            )
            .order_by(UserActivity.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

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


async def deactivate_user(db: AsyncSession, user_id: UUID) -> AdminActionResponse:
    """
    Soft delete: desactiva la cuenta.
    El usuario no puede iniciar sesión pero sus datos se conservan.
    """
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        return AdminActionResponse(ok=False, message="Usuario no encontrado")
    if not user.is_active:
        return AdminActionResponse(ok=False, message="El usuario ya está desactivado")

    user.is_active = False
    await db.commit()
    return AdminActionResponse(ok=True, message=f"Usuario {user.email} desactivado")


async def reactivate_user(db: AsyncSession, user_id: UUID) -> AdminActionResponse:
    """Reactiva una cuenta previamente desactivada."""
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        return AdminActionResponse(ok=False, message="Usuario no encontrado")

    user.is_active = True
    await db.commit()
    return AdminActionResponse(ok=True, message=f"Usuario {user.email} reactivado")


async def delete_user_hard(db: AsyncSession, user_id: UUID) -> AdminActionResponse:
    """
    Hard delete: elimina definitivamente la cuenta y TODA su actividad.
    Gracias al CASCADE en la FK, se eliminan automáticamente:
      - businesses, conversations, messages, content_calendars,
        content_pieces, subscriptions, user_activities
    ADVERTENCIA: Esta acción es irreversible.
    """
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        return AdminActionResponse(ok=False, message="Usuario no encontrado")

    email = user.email
    await db.delete(user)
    await db.commit()
    return AdminActionResponse(ok=True, message=f"Usuario {email} eliminado permanentemente")


# ── Actividad global ───────────────────────────────────────────────────────────

async def list_activity(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    user_id_filter: UUID | None = None,
    event_type_filter: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> ActivityListResponse:
    """Lista actividad global con filtros."""
    base_q = select(UserActivity, User.email).join(
        User, UserActivity.user_id == User.id
    )

    if user_id_filter:
        base_q = base_q.where(UserActivity.user_id == user_id_filter)
    if event_type_filter:
        base_q = base_q.where(UserActivity.event_type == event_type_filter)
    if date_from:
        base_q = base_q.where(UserActivity.created_at >= date_from)
    if date_to:
        base_q = base_q.where(UserActivity.created_at <= date_to)

    count_q = select(func.count()).select_from(base_q.subquery())
    total: int = (await db.execute(count_q)).scalar_one()

    offset = (page - 1) * page_size
    rows = (
        await db.execute(
            base_q.order_by(UserActivity.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
    ).all()

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
