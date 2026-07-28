import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Site(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sites"

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    owner: Mapped["User | None"] = relationship("User", back_populates="sites")
    urls: Mapped[list["Url"]] = relationship(
        "Url", back_populates="site", cascade="all, delete-orphan"
    )
    keywords: Mapped[list["Keyword"]] = relationship(
        "Keyword", back_populates="site", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="site", cascade="all, delete-orphan"
    )


from app.models.keyword import Keyword  # noqa: E402
from app.models.report import Report  # noqa: E402
from app.models.url import Url  # noqa: E402
from app.models.user import User  # noqa: E402
