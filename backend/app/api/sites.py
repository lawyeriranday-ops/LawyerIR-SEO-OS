import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import handle_service_error
from app.schemas.audit import AuditRead
from app.schemas.common import PaginatedResponse
from app.schemas.site import SiteCreate, SiteRead, SiteUpdate
from app.services.site_service import SiteService

router = APIRouter(prefix="/sites", tags=["sites"])
service = SiteService()


@router.get("", response_model=PaginatedResponse[SiteRead])
def list_sites(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = service.list_sites(db, skip=skip, limit=limit)
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("", response_model=SiteRead, status_code=201)
def create_site(data: SiteCreate, db: Session = Depends(get_db)):
    try:
        return service.create_site(db, data)
    except ValueError as exc:
        handle_service_error(exc)


@router.get("/{site_id}", response_model=SiteRead)
def get_site(site_id: uuid.UUID, db: Session = Depends(get_db)):
    site = service.get_site(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.patch("/{site_id}", response_model=SiteRead)
def update_site(site_id: uuid.UUID, data: SiteUpdate, db: Session = Depends(get_db)):
    site = service.get_site(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    try:
        return service.update_site(db, site, data)
    except ValueError as exc:
        handle_service_error(exc)


@router.delete("/{site_id}", status_code=204)
def delete_site(site_id: uuid.UUID, db: Session = Depends(get_db)):
    site = service.get_site(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    service.delete_site(db, site)
