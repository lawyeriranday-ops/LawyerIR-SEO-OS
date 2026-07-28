import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UrlStatus


class Url(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "urls"
    __table_args__ = (UniqueConstraint("site_id", "path", name="uq_urls_site_path"),)

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    full_url: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[UrlStatus] = mapped_column(
        String(20), default=UrlStatus.active, nullable=False
    )
    last_crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    site: Mapped["Site"] = relationship("Site", back_populates="urls")
    audits: Mapped[list["Audit"]] = relationship(
        "Audit", back_populates="url", cascade="all, delete-orphan"
    )
    targeted_keywords: Mapped[list["Keyword"]] = relationship(
        "Keyword", back_populates="target_url"
    )


from app.models.audit import Audit  # noqa: E402
from app.models.keyword import Keyword  # noqa: E402
from app.models.site import Site  # noqa: E402
