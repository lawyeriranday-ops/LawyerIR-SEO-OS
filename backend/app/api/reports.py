import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import handle_service_error
from app.schemas.common import PaginatedResponse
from app.schemas.report import ReportCreate, ReportRead, ReportUpdate
from app.services.report_service import ReportService
from app.services.site_service import SiteService

router = APIRouter(tags=["reports"])
report_service = ReportService()
site_service = SiteService()


@router.get("/sites/{site_id}/reports", response_model=PaginatedResponse[ReportRead])
def list_site_reports(
    site_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if not site_service.get_site(db, site_id):
        raise HTTPException(status_code=404, detail="Site not found")
    items, total = report_service.list_reports(db, site_id, skip=skip, limit=limit)
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.post("/sites/{site_id}/reports", response_model=ReportRead, status_code=201)
def create_site_report(
    site_id: uuid.UUID, data: ReportCreate, db: Session = Depends(get_db)
):
    if not site_service.get_site(db, site_id):
        raise HTTPException(status_code=404, detail="Site not found")
    try:
        return report_service.create_report(db, site_id, data)
    except ValueError as exc:
        handle_service_error(exc)


@router.get("/reports/{report_id}", response_model=ReportRead)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = report_service.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/reports/{report_id}", response_model=ReportRead)
def update_report(
    report_id: uuid.UUID, data: ReportUpdate, db: Session = Depends(get_db)
):
    report = report_service.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        return report_service.update_report(db, report, data)
    except ValueError as exc:
        handle_service_error(exc)


@router.delete("/reports/{report_id}", status_code=204)
def delete_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    report = report_service.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report_service.delete_report(db, report)
