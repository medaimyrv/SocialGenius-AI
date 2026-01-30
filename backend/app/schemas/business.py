import uuid
from datetime import datetime

from pydantic import BaseModel


class BusinessCreate(BaseModel):
    name: str
    industry: str
    description: str
    target_audience: str | None = None
    brand_voice: str | None = None
    website_url: str | None = None
    instagram_handle: str | None = None
    tiktok_handle: str | None = None
    extra_context: dict | None = None


class BusinessUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    description: str | None = None
    target_audience: str | None = None
    brand_voice: str | None = None
    website_url: str | None = None
    instagram_handle: str | None = None
    tiktok_handle: str | None = None
    extra_context: dict | None = None


class BusinessResponse(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    industry: str
    description: str
    target_audience: str | None
    brand_voice: str | None
    website_url: str | None
    instagram_handle: str | None
    tiktok_handle: str | None
    extra_context: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
