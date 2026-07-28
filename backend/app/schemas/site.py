import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SiteCreate(BaseModel):
    url: HttpUrl
    name: str = Field(min_length=1, max_length=255)
    owner_id: uuid.UUID | None = None


class SiteUpdate(BaseModel):
    url: HttpUrl | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    owner_id: uuid.UUID | None = None


class SiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID | None
    url: str
    name: str
    created_at: datetime
    updated_at: datetime
