import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import handle_service_error
from app.models.enums import UrlStatus
from app.schemas.common import PaginatedResponse
from app.schemas.url import UrlCreate, UrlRead, UrlUpdate
from app.services.site_service import SiteService
from app.services.url_service import UrlService

router = APIRouter(tags=["urls"])
site_service = SiteService()
url_service = UrlService()


@router.get("/sites/{site_id}/urls", response_model=PaginatedResponse[UrlRead])
def list_site_urls(
    site_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: UrlStatus | None = None,
    db: Session = Depends(get_db),
):
    if not site_service.get_site(db, site_id):
        raise HTTPException(status_code=404, detail="Site not found")
    items, total = url_service.list_urls(db, site_id, skip=skip, limit=limit, status=status)
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("/sites/{site_id}/urls", response_model=UrlRead, status_code=201)
def create_site_url(site_id: uuid.UUID, data: UrlCreate, db: Session = Depends(get_db)):
    if not site_service.get_site(db, site_id):
        raise HTTPException(status_code=404, detail="Site not found")
    try:
        return url_service.create_url(db, site_id, data)
    except ValueError as exc:
        handle_service_error(exc)


@router.get("/urls/{url_id}", response_model=UrlRead)
def get_url(url_id: uuid.UUID, db: Session = Depends(get_db)):
    url = url_service.get_url(db, url_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return url


@router.patch("/urls/{url_id}", response_model=UrlRead)
def update_url(url_id: uuid.UUID, data: UrlUpdate, db: Session = Depends(get_db)):
    url = url_service.get_url(db, url_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    try:
        return url_service.update_url(db, url, data)
    except ValueError as exc:
        handle_service_error(exc)


@router.delete("/urls/{url_id}", status_code=204)
def delete_url(url_id: uuid.UUID, db: Session = Depends(get_db)):
    url = url_service.get_url(db, url_id)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    url_service.delete_url(db, url)
