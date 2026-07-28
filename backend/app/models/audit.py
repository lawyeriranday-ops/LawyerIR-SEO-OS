import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.models.enums import AuditStatus


class Audit(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "audits"

    url_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("urls.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[AuditStatus] = mapped_column(
        String(50), default=AuditStatus.pending, nullable=False
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    url: Mapped["Url"] = relationship("Url", back_populates="audits")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="audit")

    @property
    def site_id(self) -> uuid.UUID:
        return self.url.site_id


from app.models.report import Report  # noqa: E402
from app.models.url import Url  # noqa: E402
