import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.enums import UrlStatus


class UrlCreate(BaseModel):
    path: str = Field(min_length=1, max_length=512)
    full_url: HttpUrl
    title: str | None = Field(default=None, max_length=512)
    meta_description: str | None = None
    status: UrlStatus = UrlStatus.active


class UrlUpdate(BaseModel):
    path: str | None = Field(default=None, min_length=1, max_length=512)
    full_url: HttpUrl | None = None
    title: str | None = Field(default=None, max_length=512)
    meta_description: str | None = None
    status: UrlStatus | None = None
    last_crawled_at: datetime | None = None


class UrlRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    site_id: uuid.UUID
    path: str
    full_url: str
    title: str | None
    meta_description: str | None
    status: UrlStatus
    last_crawled_at: datetime | None
    created_at: datetime
    updated_at: datetime
