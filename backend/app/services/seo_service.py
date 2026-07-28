"""DB-backed SEO service."""

from sqlalchemy.orm import Session

from app.models.site import Site
from app.models.url import Url


class SEOService:
    def get_site_overview(self, db: Session, site_id) -> dict:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise ValueError("Site not found")

        url_count = db.query(Url).filter(Url.site_id == site_id).count()

        return {
            "site_id": str(site.id),
            "site_url": site.url,
            "name": site.name,
            "url_count": url_count,
            "status": "ready",
        }
