import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import PlanTier, SubscriptionStatus
from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.user import User


class Subscription(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    plan_tier: Mapped[PlanTier] = mapped_column(
        SAEnum(PlanTier), default=PlanTier.FREE
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE
    )

    # Stripe
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), unique=True
    )
    stripe_price_id: Mapped[str | None] = mapped_column(String(255))
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False)

    # Usage tracking (reset monthly)
    strategies_used_this_month: Mapped[int] = mapped_column(Integer, default=0)
    calendars_used_this_month: Mapped[int] = mapped_column(Integer, default=0)
    messages_used_this_month: Mapped[int] = mapped_column(Integer, default=0)
    usage_reset_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="subscription")
