from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import KeywordIntent, KeywordPriority
from app.models.keyword import Keyword
from app.models.url import Url
from app.schemas.keyword import KeywordCreate, KeywordUpdate


class KeywordService:
    def _compute_ctr(
        self,
        clicks: int | None,
        impressions: int | None,
        ctr: Decimal | None,
    ) -> Decimal | None:
        if ctr is not None:
            return ctr
        if clicks is not None and impressions is not None and impressions > 0:
            return Decimal(clicks) / Decimal(impressions)
        return None

    def _validate_target_url(self, db: Session, site_id, target_url_id) -> None:
        if target_url_id is None:
            return
        url = db.query(Url).filter(Url.id == target_url_id).first()
        if not url:
            raise ValueError("Target URL not found")
        if url.site_id != site_id:
            raise ValueError("Target URL must belong to the same site")

    def list_keywords(
        self,
        db: Session,
        site_id,
        skip: int = 0,
        limit: int = 50,
        priority: KeywordPriority | None = None,
        intent: KeywordIntent | None = None,
    ) -> tuple[list[Keyword], int]:
        query = db.query(Keyword).filter(Keyword.site_id == site_id)
        if priority is not None:
            query = query.filter(Keyword.priority == priority)
        if intent is not None:
            query = query.filter(Keyword.intent == intent)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_keyword(self, db: Session, keyword_id) -> Keyword | None:
        return db.query(Keyword).filter(Keyword.id == keyword_id).first()

    def create_keyword(self, db: Session, site_id, data: KeywordCreate) -> Keyword:
        existing = (
            db.query(Keyword)
            .filter(Keyword.site_id == site_id, Keyword.keyword == data.keyword)
            .first()
        )
        if existing:
            raise ValueError("Keyword already exists for this site")

        self._validate_target_url(db, site_id, data.target_url_id)

        ctr = self._compute_ctr(data.clicks, data.impressions, data.ctr)

        keyword = Keyword(
            site_id=site_id,
            target_url_id=data.target_url_id,
            keyword=data.keyword,
            search_volume=data.search_volume,
            position=data.position,
            clicks=data.clicks,
            impressions=data.impressions,
            ctr=ctr,
            intent=data.intent,
            priority=data.priority,
        )
        db.add(keyword)
        db.commit()
        db.refresh(keyword)
        return keyword

    def update_keyword(self, db: Session, keyword: Keyword, data: KeywordUpdate) -> Keyword:
        if data.keyword is not None and data.keyword != keyword.keyword:
            existing = (
                db.query(Keyword)
                .filter(
                    Keyword.site_id == keyword.site_id,
                    Keyword.keyword == data.keyword,
                    Keyword.id != keyword.id,
                )
                .first()
            )
            if existing:
                raise ValueError("Keyword already exists for this site")
            keyword.keyword = data.keyword

        if data.target_url_id is not None:
            self._validate_target_url(db, keyword.site_id, data.target_url_id)
            keyword.target_url_id = data.target_url_id

        if data.search_volume is not None:
            keyword.search_volume = data.search_volume
        if data.position is not None:
            keyword.position = data.position
        if data.clicks is not None:
            keyword.clicks = data.clicks
        if data.impressions is not None:
            keyword.impressions = data.impressions
        if data.intent is not None:
            keyword.intent = data.intent
        if data.priority is not None:
            keyword.priority = data.priority

        clicks = keyword.clicks
        impressions = keyword.impressions
        if data.ctr is not None:
            keyword.ctr = data.ctr
        else:
            keyword.ctr = self._compute_ctr(clicks, impressions, keyword.ctr)

        db.commit()
        db.refresh(keyword)
        return keyword

    def delete_keyword(self, db: Session, keyword: Keyword) -> None:
        db.delete(keyword)
        db.commit()
