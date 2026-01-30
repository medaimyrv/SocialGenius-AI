from pydantic import BaseModel


class ContentPieceAI(BaseModel):
    day_of_week: str
    platform: str
    content_format: str
    topic: str
    caption: str
    hashtags: list[str]
    hook: str | None = None
    visual_description: str | None = None
    call_to_action: str | None = None
    scheduled_time: str  # "HH:MM"


class WeeklyCalendarAI(BaseModel):
    strategy_summary: str
    content_pieces: list[ContentPieceAI]
