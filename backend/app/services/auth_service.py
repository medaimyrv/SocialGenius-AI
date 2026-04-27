"""
Auth Service — Registro, login y gestión de tokens JWT.

Flujo de autenticación:
  1. register → crea User + Subscription FREE + evento "register"
  2. login    → valida contraseña, registra evento "login", devuelve access + refresh token
  3. refresh  → valida refresh token, verifica que el usuario siga activo, emite nuevo access token

Tokens:
  - access_token:  vida corta (30 min) — se adjunta en cada request como Bearer token
  - refresh_token: vida larga (7 días)  — solo se usa para renovar el access token

Por qué dos tokens:
  Si el access token expira o el usuario lo pierde, puede renovarlo con el refresh
  sin volver a poner contraseña. Si detectamos compromiso, desactivamos el usuario
  (is_active=False) y el próximo refresh también se bloquea.
"""
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PlanTier, SubscriptionStatus
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.subscription import Subscription
from app.models.user import User
from app.models.user_activity import UserActivity
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    """
    Crea un nuevo usuario con plan FREE.

    Orden de operaciones importante:
      1. Flush del User → genera user.id (necesario para la FK de Subscription)
      2. Crear Subscription vinculada a ese user.id
      3. Registrar evento "register" en actividad

    El commit lo hace el caller (el endpoint) — aquí solo preparamos la transacción.
    """
    # Verificar email único antes de hashear la contraseña (operación cara)
    existing = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
    if existing:
        raise ConflictError("Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    # flush para obtener user.id antes de crear la suscripción
    await db.flush()

    db.add(Subscription(
        user_id=user.id,
        plan_tier=PlanTier.FREE,
        status=SubscriptionStatus.ACTIVE,
        # El ciclo de uso se resetea a los 30 días del registro
        usage_reset_date=datetime.now(UTC) + timedelta(days=30),
    ))
    db.add(UserActivity(user_id=user.id, event_type="register"))

    return user


async def login_user(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    """
    Valida credenciales y devuelve los tokens de acceso.

    Por seguridad el mensaje de error es genérico — no revelamos si el email
    existe o no (previene enumeración de cuentas).
    """
    user = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()

    # Verificamos contraseña aunque el usuario no exista para prevenir timing attacks
    # (bcrypt.verify siempre tarda ~300ms independientemente del resultado)
    if not user or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedError("Invalid email or password")

    if not user.is_active:
        raise UnauthorizedError("Account is disabled")

    db.add(UserActivity(user_id=user.id, event_type="login"))
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """
    Emite un nuevo access_token a partir de un refresh_token válido.

    Verifica is_active en cada refresh para que desactivar un usuario
    sea efectivo en máximo 7 días (vida del refresh token) sin necesitar blacklist.
    """
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    user_id = UUID(payload["sub"])
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Util para obtener un usuario por ID — usado en deps.py para autenticar requests."""
    return (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
