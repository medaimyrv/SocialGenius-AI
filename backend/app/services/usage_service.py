from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PLAN_LIMITS, ConversationType, PlanTier
from app.core.exceptions import UsageLimitError
from app.models.subscription import Subscription

# Map conversation types to usage counter fields
USAGE_MAP = {
    ConversationType.CONTENT_STRATEGY: "strategies",
    ConversationType.CALENDAR_CREATION: "calendars",
    ConversationType.HASHTAG_RESEARCH: "strategies",
}


async def get_subscription(db: AsyncSession, user_id: UUID) -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        # Create default free subscription
        sub = Subscription(
            user_id=user_id,
            plan_tier=PlanTier.FREE,
            usage_reset_date=datetime.now(UTC) + timedelta(days=30),
        )
        db.add(sub)
        await db.flush()
    return sub


async def check_and_reset_usage(db: AsyncSession, sub: Subscription) -> None:
    if sub.usage_reset_date and datetime.now(UTC) >= sub.usage_reset_date:
        sub.strategies_used_this_month = 0
        sub.calendars_used_this_month = 0
        sub.messages_used_this_month = 0
        sub.usage_reset_date = datetime.now(UTC) + timedelta(days=30)
        await db.flush()


async def check_message_limit(db: AsyncSession, user_id: UUID) -> None:
    sub = await get_subscription(db, user_id)
    await check_and_reset_usage(db, sub)

    limits = PLAN_LIMITS[sub.plan_tier]
    max_messages = limits["max_messages_per_month"]
    if max_messages is not None and sub.messages_used_this_month >= max_messages:
        raise UsageLimitError(
            f"Has alcanzado el limite de {max_messages} mensajes/mes. "
            "Actualiza a Pro para mensajes ilimitados."
        )


async def check_business_limit(db: AsyncSession, user_id: UUID, current_count: int) -> None:
    sub = await get_subscription(db, user_id)
    limits = PLAN_LIMITS[sub.plan_tier]
    max_biz = limits["max_businesses"]
    if max_biz is not None and current_count >= max_biz:
        raise UsageLimitError(
            f"Has alcanzado el limite de {max_biz} negocio(s). "
            "Actualiza a Pro para negocios ilimitados."
        )


async def increment_message_usage(db: AsyncSession, user_id: UUID) -> None:
    sub = await get_subscription(db, user_id)
    sub.messages_used_this_month += 1
    await db.flush()


async def increment_strategy_usage(db: AsyncSession, user_id: UUID) -> None:
    sub = await get_subscription(db, user_id)
    sub.strategies_used_this_month += 1
    await db.flush()


async def increment_calendar_usage(db: AsyncSession, user_id: UUID) -> None:
    sub = await get_subscription(db, user_id)
    sub.calendars_used_this_month += 1
    await db.flush()
