"""Publisher routes package."""

from fastapi import APIRouter
from app.routes.publisher.dashboard import router as dashboard_router
from app.routes.publisher.products import router as products_router
from app.routes.publisher.import_routes import router as import_router

router = APIRouter(prefix="/publisher", tags=["publisher"])

# Include all sub-routers
router.include_router(dashboard_router)
router.include_router(products_router)
router.include_router(import_router)
