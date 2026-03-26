import logging

import httpx
from fastapi import APIRouter, BackgroundTasks

from app.api.deps import DB, CurrentUser
from app.config import settings
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


async def _notify_n8n_register(user: User) -> None:
    """Envía los datos del nuevo usuario al webhook de n8n. Falla silenciosamente."""
    if not settings.N8N_WEBHOOK_REGISTER:
        return
    payload = {
        "event": "user_registered",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(settings.N8N_WEBHOOK_REGISTER, json=payload)
            logger.info(f"n8n webhook notified: status={resp.status_code}")
    except Exception as e:
        logger.warning(f"n8n webhook failed (non-fatal): {e}")


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, db: DB, background_tasks: BackgroundTasks):
    user = await auth_service.register_user(db, data)
    background_tasks.add_task(_notify_n8n_register, user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: DB):
    return await auth_service.login_user(db, data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db: DB):
    return await auth_service.refresh_access_token(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    return current_user
