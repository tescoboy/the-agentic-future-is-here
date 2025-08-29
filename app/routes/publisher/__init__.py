"""Publisher routes package."""

from fastapi import APIRouter
from app.routes.publisher.dashboard import router as dashboard_router, _get_tenant_or_404
from app.routes.publisher.products import router as products_router
from app.routes.publisher.import_routes import router as import_router
from app.repos.products import list_products, create_product
from app.utils.csv_utils import parse_csv_file, import_products_from_csv
from app.services.sales_contract import get_default_sales_prompt

router = APIRouter(prefix="/publisher", tags=["publisher"])

# Include all sub-routers
router.include_router(dashboard_router)
router.include_router(products_router)
router.include_router(import_router)

# Export commonly used functions
__all__ = [
    "router", 
    "_get_tenant_or_404", 
    "list_products", 
    "create_product",
    "parse_csv_file",
    "import_products_from_csv",
    "get_default_sales_prompt"
]
