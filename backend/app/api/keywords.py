import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import handle_service_error
from app.models.enums import KeywordIntent, KeywordPriority
from app.schemas.common import PaginatedResponse
from app.schemas.keyword import KeywordCreate, KeywordRead, KeywordUpdate
from app.services.keyword_service import KeywordService
from app.services.site_service import SiteService

router = APIRouter(tags=["keywords"])
keyword_service = KeywordService()
site_service = SiteService()


@router.get("/sites/{site_id}/keywords", response_model=PaginatedResponse[KeywordRead])
def list_site_keywords(
    site_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    priority: KeywordPriority | None = None,
    intent: KeywordIntent | None = None,
    db: Session = Depends(get_db),
):
    if not site_service.get_site(db, site_id):
        raise HTTPException(status_code=404, detail="Site not found")
    items, total = keyword_service.list_keywords(
        db, site_id, skip=skip, limit=limit, priority=priority, intent=intent
    )
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("/sites/{site_id}/keywords", response_model=KeywordRead, status_code=201)
def create_site_keyword(
    site_id: uuid.UUID, data: KeywordCreate, db: Session = Depends(get_db)
):
    if not site_service.get_site(db, site_id):
        raise HTTPException(status_code=404, detail="Site not found")
    try:
        return keyword_service.create_keyword(db, site_id, data)
    except ValueError as exc:
        handle_service_error(exc)


@router.get("/keywords/{keyword_id}", response_model=KeywordRead)
def get_keyword(keyword_id: uuid.UUID, db: Session = Depends(get_db)):
    keyword = keyword_service.get_keyword(db, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.patch("/keywords/{keyword_id}", response_model=KeywordRead)
def update_keyword(
    keyword_id: uuid.UUID, data: KeywordUpdate, db: Session = Depends(get_db)
):
    keyword = keyword_service.get_keyword(db, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    try:
        return keyword_service.update_keyword(db, keyword, data)
    except ValueError as exc:
        handle_service_error(exc)


@router.delete("/keywords/{keyword_id}", status_code=204)
def delete_keyword(keyword_id: uuid.UUID, db: Session = Depends(get_db)):
    keyword = keyword_service.get_keyword(db, keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    keyword_service.delete_keyword(db, keyword)
