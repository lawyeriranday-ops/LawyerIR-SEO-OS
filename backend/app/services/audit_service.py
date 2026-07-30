import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.audit import Audit
from app.models.enums import AuditStatus
from app.models.url import Url
from app.schemas.audit import AuditCreate, AuditUpdate
from app.services.seo_engine import SEOAuditEngine, SEOAuditConfig


def encode_audit_summary(data: dict) -> str:
    """Helper to isolate JSON serialization of audit results into text Audit.summary."""
    return json.dumps(data, ensure_ascii=False)


def decode_audit_summary(summary: str | None) -> dict:
    """Helper to isolate JSON deserialization from text Audit.summary."""
    if not summary:
        return {}
    try:
        return json.loads(summary)
    except (json.JSONDecodeError, TypeError):
        return {"raw_summary": summary}


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

    def run_audit_for_url(
        self,
        db: Session,
        url_id,
        html_content: str | None = None,
        config: SEOAuditConfig | None = None,
        target_keyword: str | None = None,
    ) -> Audit:
        """Executes SEO audit engine analysis for a URL record and persists results."""
        url = db.query(Url).filter(Url.id == url_id).first()
        if not url:
            raise ValueError("URL not found")

        engine = SEOAuditEngine()

        if html_content is not None:
            result = engine.analyze_html(
                html=html_content,
                base_url=url.full_url,
                config=config,
                target_keyword=target_keyword,
            )
        else:
            try:
                result = asyncio.run(
                    engine.fetch_and_analyze(
                        url=url.full_url,
                        config=config,
                        target_keyword=target_keyword,
                    )
                )
            except RuntimeError:
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(
                    engine.fetch_and_analyze(
                        url=url.full_url,
                        config=config,
                        target_keyword=target_keyword,
                    )
                )

        metrics = result.get("metrics", {})
        if metrics.get("title"):
            url.title = metrics["title"]
        if metrics.get("meta_description"):
            url.meta_description = metrics["meta_description"]
        url.last_crawled_at = datetime.now(timezone.utc)

        status = AuditStatus.completed if not result.get("error") else AuditStatus.failed

        audit = Audit(
            url_id=url_id,
            status=status,
            score=result.get("score"),
            summary=encode_audit_summary(result),
        )
        db.add(audit)
        db.commit()
        return self.get_audit(db, audit.id)

    async def async_run_audit_for_url(
        self,
        db: Session,
        url_id,
        html_content: str | None = None,
        config: SEOAuditConfig | None = None,
        target_keyword: str | None = None,
    ) -> Audit:
        """Async version of run_audit_for_url for async FastAPI endpoints."""
        url = db.query(Url).filter(Url.id == url_id).first()
        if not url:
            raise ValueError("URL not found")

        engine = SEOAuditEngine()

        if html_content is not None:
            result = engine.analyze_html(
                html=html_content,
                base_url=url.full_url,
                config=config,
                target_keyword=target_keyword,
            )
        else:
            result = await engine.fetch_and_analyze(
                url=url.full_url,
                config=config,
                target_keyword=target_keyword,
            )

        metrics = result.get("metrics", {})
        if metrics.get("title"):
            url.title = metrics["title"]
        if metrics.get("meta_description"):
            url.meta_description = metrics["meta_description"]
        url.last_crawled_at = datetime.now(timezone.utc)

        status = AuditStatus.completed if not result.get("error") else AuditStatus.failed

        audit = Audit(
            url_id=url_id,
            status=status,
            score=result.get("score"),
            summary=encode_audit_summary(result),
        )
        db.add(audit)
        db.commit()
        return self.get_audit(db, audit.id)

