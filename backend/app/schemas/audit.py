import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AuditStatus


class AuditCreate(BaseModel):
    status: AuditStatus = AuditStatus.pending
    score: int | None = Field(default=None, ge=0, le=100)
    summary: str | None = None


class AuditUpdate(BaseModel):
    status: AuditStatus | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    summary: str | None = None


class AuditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url_id: uuid.UUID
    site_id: uuid.UUID
    status: AuditStatus
    score: int | None
    summary: str | None
    created_at: datetime