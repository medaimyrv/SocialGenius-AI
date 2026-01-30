import enum


class PlanTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    INACTIVE = "inactive"


class ConversationType(str, enum.Enum):
    BUSINESS_ANALYSIS = "business_analysis"
    CONTENT_STRATEGY = "content_strategy"
    CALENDAR_CREATION = "calendar_creation"
    COPYWRITING = "copywriting"
    HASHTAG_RESEARCH = "hashtag_research"
    GENERAL = "general"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ContentFormat(str, enum.Enum):
    REEL = "reel"
    CAROUSEL = "carousel"
    SINGLE_IMAGE = "single_image"
    STORY = "story"
    TIKTOK_VIDEO = "tiktok_video"
    LIVE = "live"


class Platform(str, enum.Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


# Freemium limits
PLAN_LIMITS = {
    PlanTier.FREE: {
        "max_businesses": 1,
        "max_strategies_per_month": 3,
        "max_calendars_per_month": 2,
        "max_messages_per_month": 50,
        "max_hashtag_research_per_month": 3,
        "can_export_calendar": False,
        "can_edit_content": False,
        "allowed_models": ["gpt-4o-mini"],
    },
    PlanTier.PRO: {
        "max_businesses": None,
        "max_strategies_per_month": None,
        "max_calendars_per_month": None,
        "max_messages_per_month": None,
        "max_hashtag_research_per_month": None,
        "can_export_calendar": True,
        "can_edit_content": True,
        "allowed_models": ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20241022"],
    },
}
