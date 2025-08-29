"""Preflight routes package."""

from fastapi import APIRouter
from app.routes.preflight.endpoints import router as endpoints_router

router = APIRouter(prefix="/preflight", tags=["preflight"])

# Include all sub-routers
router.include_router(endpoints_router)

