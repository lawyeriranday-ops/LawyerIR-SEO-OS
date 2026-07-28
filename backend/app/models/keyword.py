import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import KeywordIntent, KeywordPriority


class Keyword(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "keywords"
    __table_args__ = (UniqueConstraint("site_id", "keyword", name="uq_keywords_site_keyword"),)

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sites.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_url_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("urls.id", ondelete="SET NULL"),
        nullable=True,
    )
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    search_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    clicks: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    impressions: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    ctr: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    intent: Mapped[KeywordIntent | None] = mapped_column(String(20), nullable=True)
    priority: Mapped[KeywordPriority] = mapped_column(
        String(10), default=KeywordPriority.medium, nullable=False
    )

    site: Mapped["Site"] = relationship("Site", back_populates="keywords")
    target_url: Mapped["Url | None"] = relationship("Url", back_populates="targeted_keywords")


from app.models.site import Site  # noqa: E402
from app.models.url import Url  # noqa: E402
