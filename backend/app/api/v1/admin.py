"""
Panel de Administración — endpoints protegidos por role='admin'.

Rutas:
  GET    /admin/users                  → listado con filtros y paginación
  GET    /admin/users/{user_id}        → detalle + contadores
  PATCH  /admin/users/{user_id}/deactivate  → soft delete
  PATCH  /admin/users/{user_id}/reactivate  → reactivar cuenta
  DELETE /admin/users/{user_id}        → hard delete (irreversible)
  GET    /admin/activity               → actividad global con filtros
"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import DB, AdminUser
from app.core.exceptions import NotFoundError
from app.schemas.admin import (
    ActivityListResponse,
    AdminActionResponse,
    AdminUserDetail,
    AdminUserListResponse,
)
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    _: AdminUser,
    db: DB,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    email: str | None = Query(None),
    role: str | None = Query(None, pattern="^(user|admin)$"),
    is_active: bool | None = Query(None),
):
    """Lista todos los usuarios. Solo accesible por admins."""
    return await admin_service.list_users(
        db,
        page=page,
        page_size=page_size,
        email_filter=email,
        role_filter=role,
        is_active_filter=is_active,
    )


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_user_detail(user_id: UUID, _: AdminUser, db: DB):
    """Detalle completo de un usuario con sus métricas."""
    detail = await admin_service.get_user_detail(db, user_id)
    if not detail:
        raise NotFoundError("Usuario no encontrado")
    return detail


@router.patch("/users/{user_id}/deactivate", response_model=AdminActionResponse)
async def deactivate_user(user_id: UUID, _: AdminUser, db: DB):
    """
    Soft delete: desactiva la cuenta.
    El usuario no podrá iniciar sesión pero sus datos se conservan.
    """
    return await admin_service.deactivate_user(db, user_id)


@router.patch("/users/{user_id}/reactivate", response_model=AdminActionResponse)
async def reactivate_user(user_id: UUID, _: AdminUser, db: DB):
    """Reactiva una cuenta previamente desactivada."""
    return await admin_service.reactivate_user(db, user_id)


@router.delete("/users/{user_id}", response_model=AdminActionResponse)
async def delete_user(user_id: UUID, _: AdminUser, db: DB):
    """
    Hard delete: elimina definitivamente al usuario y TODOS sus datos.
    Acción IRREVERSIBLE — requiere confirmación en el frontend.
    """
    return await admin_service.delete_user_hard(db, user_id)


@router.get("/activity", response_model=ActivityListResponse)
async def list_activity(
    _: AdminUser,
    db: DB,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: UUID | None = Query(None),
    event_type: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
):
    """Actividad global con filtros por usuario, tipo de evento y fechas."""
    return await admin_service.list_activity(
        db,
        page=page,
        page_size=page_size,
        user_id_filter=user_id,
        event_type_filter=event_type,
        date_from=date_from,
        date_to=date_to,
    )
