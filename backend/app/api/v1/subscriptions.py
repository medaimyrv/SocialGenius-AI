from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.core.constants import PLAN_LIMITS
from app.schemas.subscription import SubscriptionStatusResponse
from app.services.usage_service import get_subscription

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_status(db: DB, current_user: CurrentUser):
    sub = await get_subscription(db, current_user.id)
    limits = PLAN_LIMITS[sub.plan_tier]

    return SubscriptionStatusResponse(
        plan_tier=sub.plan_tier,
        status=sub.status,
        strategies_used_this_month=sub.strategies_used_this_month,
        calendars_used_this_month=sub.calendars_used_this_month,
        messages_used_this_month=sub.messages_used_this_month,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        max_strategies=limits["max_strategies_per_month"],
        max_calendars=limits["max_calendars_per_month"],
        max_messages=limits["max_messages_per_month"],
        can_export_calendar=limits["can_export_calendar"],
        can_edit_content=limits["can_edit_content"],
    )
