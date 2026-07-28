from sqlalchemy.orm import Session, joinedload

from app.models.audit import Audit
from app.models.report import Report
from app.models.url import Url
from app.schemas.report import ReportCreate, ReportUpdate


class ReportService:
    def list_reports(
        self, db: Session, site_id, skip: int = 0, limit: int = 50
    ) -> tuple[list[Report], int]:
        query = db.query(Report).filter(Report.site_id == site_id)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_report(self, db: Session, report_id) -> Report | None:
        return db.query(Report).filter(Report.id == report_id).first()

    def _validate_audit(self, db: Session, site_id, audit_id) -> None:
        if audit_id is None:
            return
        audit = (
            db.query(Audit)
            .options(joinedload(Audit.url))
            .filter(Audit.id == audit_id)
            .first()
        )
        if not audit:
            raise ValueError("Audit not found")
        if audit.url.site_id != site_id:
            raise ValueError("Audit must belong to the same site")

    def create_report(self, db: Session, site_id, data: ReportCreate) -> Report:
        self._validate_audit(db, site_id, data.audit_id)

        report = Report(
            site_id=site_id,
            audit_id=data.audit_id,
            title=data.title,
            content=data.content,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def update_report(self, db: Session, report: Report, data: ReportUpdate) -> Report:
        if data.audit_id is not None:
            self._validate_audit(db, report.site_id, data.audit_id)
            report.audit_id = data.audit_id

        if data.title is not None:
            report.title = data.title
        if data.content is not None:
            report.content = data.content

        db.commit()
        db.refresh(report)
        return report

    def delete_report(self, db: Session, report: Report) -> None:
        db.delete(report)
        db.commit()
