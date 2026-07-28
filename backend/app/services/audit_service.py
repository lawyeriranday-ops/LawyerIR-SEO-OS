from sqlalchemy.orm import Session, joinedload

from app.models.audit import Audit
from app.models.url import Url
from app.schemas.audit import AuditCreate, AuditUpdate


class AuditService:
    def _base_query(self, db: Session):
        return db.query(Audit).options(joinedload(Audit.url))

    def list_audits_by_url(
        self, db: Session, url_id, skip: int = 0, limit: int = 50
    ) -> tuple[list[Audit], int]:
        query = self._base_query(db).filter(Audit.url_id == url_id)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def list_audits_by_site(
        self, db: Session, site_id, skip: int = 0, limit: int = 50
    ) -> tuple[list[Audit], int]:
        query = (
            self._base_query(db)
            .join(Url)
            .filter(Url.site_id == site_id)
        )
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_audit(self, db: Session, audit_id) -> Audit | None:
        return self._base_query(db).filter(Audit.id == audit_id).first()

    def create_audit(self, db: Session, url_id, data: AuditCreate) -> Audit:
        url = db.query(Url).filter(Url.id == url_id).first()
        if not url:
            raise ValueError("URL not found")

        audit = Audit(
            url_id=url_id,
            status=data.status,
            score=data.score,
            summary=data.summary,
        )
        db.add(audit)
        db.commit()
        audit = self.get_audit(db, audit.id)
        return audit

    def update_audit(self, db: Session, audit: Audit, data: AuditUpdate) -> Audit:
        if data.status is not None:
            audit.status = data.status
        if data.score is not None:
            audit.score = data.score
        if data.summary is not None:
            audit.summary = data.summary

        db.commit()
        audit = self.get_audit(db, audit.id)
        return audit

    def delete_audit(self, db: Session, audit: Audit) -> None:
        db.delete(audit)
        db.commit()
