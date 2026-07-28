from fastapi import APIRouter

from app.api.audits import router as audits_router
from app.api.keywords import router as keywords_router
from app.api.reports import router as reports_router
from app.api.sites import router as sites_router
from app.api.urls import router as urls_router
from app.api.users import router as users_router

router = APIRouter(prefix="/api/v1")

router.include_router(sites_router)
router.include_router(urls_router)
router.include_router(audits_router)
router.include_router(keywords_router)
router.include_router(reports_router)
router.include_router(users_router)


@router.get("/status")
async def api_status():
    return {"service": "LawyerIR SEO OS", "ready": True}
