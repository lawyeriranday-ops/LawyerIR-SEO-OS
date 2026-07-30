import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import handle_service_error
from app.schemas.audit import AuditCreate, AuditRead, AuditRunRequest, AuditUpdate
from app.schemas.common import PaginatedResponse
from app.services.audit_service import AuditService
from app.services.site_service import SiteService
from app.services.url_service import UrlService

router = APIRouter(tags=["audits"])
audit_service = AuditService()
url_service = UrlService()
site_service = SiteService()


def _audit_to_read(audit) -> AuditRead:
    return AuditRead(
        id=audit.id,
        url_id=audit.url_id,
        site_id=audit.site_id,
        status=audit.status,
        score=audit.score,
        summary=audit.summary,
        created_at=audit.created_at,
    )


@router.get("/urls/{url_id}/audits", response_model=PaginatedResponse[AuditRead])
def list_url_audits(
    url_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if not url_service.get_url(db, url_id):
        raise HTTPException(status_code=404, detail="URL not found")
    items, total = audit_service.list_audits_by_url(db, url_id, skip=skip, limit=limit)
    return PaginatedResponse(
        items=[_audit_to_read(a) for a in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/sites/{site_id}/audits", response_model=PaginatedResponse[AuditRead])
def list_site_audits(
    site_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if not site_service.get_site(db, site_id):
        raise HTTPException(status_code=404, detail="Site not found")
    items, total = audit_service.list_audits_by_site(db, site_id, skip=skip, limit=limit)
    return PaginatedResponse(
        items=[_audit_to_read(a) for a in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/urls/{url_id}/audits", response_model=AuditRead, status_code=201)
def create_url_audit(url_id: uuid.UUID, data: AuditCreate, db: Session = Depends(get_db)):
    try:
        audit = audit_service.create_audit(db, url_id, data)
        return _audit_to_read(audit)
    except ValueError as exc:
        handle_service_error(exc)


@router.post("/urls/{url_id}/audits/run", response_model=AuditRead, status_code=201)
async def run_url_audit(
    url_id: uuid.UUID,
    payload: AuditRunRequest | None = None,
    db: Session = Depends(get_db),
):
    html_content = payload.html_content if payload else None
    try:
        audit = await audit_service.async_run_audit_for_url(db, url_id, html_content=html_content)
        return _audit_to_read(audit)
    except ValueError as exc:
        handle_service_error(exc)


@router.get("/audits/{audit_id}", response_model=AuditRead)
def get_audit(audit_id: uuid.UUID, db: Session = Depends(get_db)):
    audit = audit_service.get_audit(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return _audit_to_read(audit)


@router.patch("/audits/{audit_id}", response_model=AuditRead)
def update_audit(audit_id: uuid.UUID, data: AuditUpdate, db: Session = Depends(get_db)):
    audit = audit_service.get_audit(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    audit = audit_service.update_audit(db, audit, data)
    return _audit_to_read(audit)


@router.delete("/audits/{audit_id}", status_code=204)
def delete_audit(audit_id: uuid.UUID, db: Session = Depends(get_db)):
    audit = audit_service.get_audit(db, audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    audit_service.delete_audit(db, audit)
