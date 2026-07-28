from sqlalchemy.orm import Session

from app.models.enums import UrlStatus
from app.models.url import Url
from app.schemas.url import UrlCreate, UrlUpdate


class UrlService:
    def list_urls(
        self,
        db: Session,
        site_id,
        skip: int = 0,
        limit: int = 50,
        status: UrlStatus | None = None,
    ) -> tuple[list[Url], int]:
        query = db.query(Url).filter(Url.site_id == site_id)
        if status is not None:
            query = query.filter(Url.status == status)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_url(self, db: Session, url_id) -> Url | None:
        return db.query(Url).filter(Url.id == url_id).first()

    def create_url(self, db: Session, site_id, data: UrlCreate) -> Url:
        full_url_str = str(data.full_url)

        existing_path = (
            db.query(Url)
            .filter(Url.site_id == site_id, Url.path == data.path)
            .first()
        )
        if existing_path:
            raise ValueError("URL path already exists for this site")

        existing_full = db.query(Url).filter(Url.full_url == full_url_str).first()
        if existing_full:
            raise ValueError("Full URL already exists")

        url = Url(
            site_id=site_id,
            path=data.path,
            full_url=full_url_str,
            title=data.title,
            meta_description=data.meta_description,
            status=data.status,
        )
        db.add(url)
        db.commit()
        db.refresh(url)
        return url

    def update_url(self, db: Session, url: Url, data: UrlUpdate) -> Url:
        if data.path is not None and data.path != url.path:
            existing_path = (
                db.query(Url)
                .filter(Url.site_id == url.site_id, Url.path == data.path)
                .first()
            )
            if existing_path:
                raise ValueError("URL path already exists for this site")
            url.path = data.path

        if data.full_url is not None:
            full_url_str = str(data.full_url)
            existing_full = (
                db.query(Url)
                .filter(Url.full_url == full_url_str, Url.id != url.id)
                .first()
            )
            if existing_full:
                raise ValueError("Full URL already exists")
            url.full_url = full_url_str

        if data.title is not None:
            url.title = data.title
        if data.meta_description is not None:
            url.meta_description = data.meta_description
        if data.status is not None:
            url.status = data.status
        if data.last_crawled_at is not None:
            url.last_crawled_at = data.last_crawled_at

        db.commit()
        db.refresh(url)
        return url

    def delete_url(self, db: Session, url: Url) -> None:
        db.delete(url)
        db.commit()
