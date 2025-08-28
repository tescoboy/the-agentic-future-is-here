"""Tenant routes package."""

from fastapi import APIRouter
from app.routes.tenants.crud import router as crud_router
from app.routes.tenants.prompt import router as prompt_router

router = APIRouter(prefix="/tenants", tags=["tenants"])

# Include all sub-routers
router.include_router(crud_router)
router.include_router(prompt_router)
