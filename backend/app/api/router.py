from fastapi import APIRouter

from app.api.companies import router as companies_router
from app.api.events import router as events_router
from app.api.health import router as health_router
from app.api.hedge import router as hedge_router
from app.api.impacts import router as impacts_router
from app.api.users import router as users_router

router = APIRouter()
router.include_router(health_router)
router.include_router(events_router)
router.include_router(companies_router)
router.include_router(hedge_router)
router.include_router(impacts_router)
router.include_router(users_router)
