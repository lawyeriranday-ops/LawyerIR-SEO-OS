from sqlalchemy.orm import Session

from app.models.site import Site
from app.models.user import User
from app.schemas.site import SiteCreate, SiteUpdate


class SiteService:
    def list_sites(self, db: Session, skip: int = 0, limit: int = 50) -> tuple[list[Site], int]:
        query = db.query(Site)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_site(self, db: Session, site_id) -> Site | None:
        return db.query(Site).filter(Site.id == site_id).first()

    def get_by_url(self, db: Session, url: str) -> Site | None:
        return db.query(Site).filter(Site.url == url).first()

    def create_site(self, db: Session, data: SiteCreate) -> Site:
        url_str = str(data.url).rstrip("/")
        if self.get_by_url(db, url_str):
            raise ValueError("Site URL already exists")

        if data.owner_id is not None:
            owner = db.query(User).filter(User.id == data.owner_id).first()
            if not owner:
                raise ValueError("Owner user not found")

        site = Site(url=url_str, name=data.name, owner_id=data.owner_id)
        db.add(site)
        db.commit()
        db.refresh(site)
        return site

    def update_site(self, db: Session, site: Site, data: SiteUpdate) -> Site:
        if data.url is not None:
            url_str = str(data.url).rstrip("/")
            existing = self.get_by_url(db, url_str)
            if existing and existing.id != site.id:
                raise ValueError("Site URL already exists")
            site.url = url_str

        if data.name is not None:
            site.name = data.name

        if data.owner_id is not None:
            owner = db.query(User).filter(User.id == data.owner_id).first()
            if not owner:
                raise ValueError("Owner user not found")
            site.owner_id = data.owner_id

        db.commit()
        db.refresh(site)
        return site

    def delete_site(self, db: Session, site: Site) -> None:
        db.delete(site)
        db.commit()
