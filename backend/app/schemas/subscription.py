from datetime import datetime

from pydantic import BaseModel

from app.core.constants import PlanTier, SubscriptionStatus


class SubscriptionStatusResponse(BaseModel):
    plan_tier: PlanTier
    status: SubscriptionStatus
    strategies_used_this_month: int
    calendars_used_this_month: int
    messages_used_this_month: int
    current_period_end: datetime | None
    cancel_at_period_end: bool

    # Computed limits
    max_strategies: int | None
    max_calendars: int | None
    max_messages: int | None
    can_export_calendar: bool
    can_edit_content: bool

    model_config = {"from_attributes": True}


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class PortalSessionResponse(BaseModel):
    portal_url: str
