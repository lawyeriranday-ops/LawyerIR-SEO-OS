import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import KeywordIntent, KeywordPriority


class KeywordCreate(BaseModel):
    keyword: str = Field(min_length=1, max_length=255)
    target_url_id: uuid.UUID | None = None
    search_volume: int | None = Field(default=None, ge=0)
    position: Decimal | None = Field(default=None, ge=0)
    clicks: int | None = Field(default=0, ge=0)
    impressions: int | None = Field(default=0, ge=0)
    ctr: Decimal | None = Field(default=None, ge=0, le=1)
    intent: KeywordIntent | None = None
    priority: KeywordPriority = KeywordPriority.medium


class KeywordUpdate(BaseModel):
    keyword: str | None = Field(default=None, min_length=1, max_length=255)
    target_url_id: uuid.UUID | None = None
    search_volume: int | None = Field(default=None, ge=0)
    position: Decimal | None = Field(default=None, ge=0)
    clicks: int | None = Field(default=None, ge=0)
    impressions: int | None = Field(default=None, ge=0)
    ctr: Decimal | None = Field(default=None, ge=0, le=1)
    intent: KeywordIntent | None = None
    priority: KeywordPriority | None = None


class KeywordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    site_id: uuid.UUID
    target_url_id: uuid.UUID | None
    keyword: str
    search_volume: int | None
    position: Decimal | None
    clicks: int | None
    impressions: int | None
    ctr: Decimal | None
    intent: KeywordIntent | None
    priority: KeywordPriority
    created_at: datetime
    updated_at: datetime
