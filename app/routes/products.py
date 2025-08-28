"""Product routes for admin interface."""

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db import get_session
from app.repos.products import list_products
from app.utils.pagination import create_pagination_info, build_page_urls

router = APIRouter(prefix="/products", tags=["products"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def list_products_view(request: Request, session: Session = Depends(get_session),
                      q: str = "", sort: str = "created_at", order: str = "desc",
                      page: int = 1, page_size: int = 20):
    """List products with search, sort, and pagination."""
    # Clamp page_size
    page_size = max(1, min(page_size, 100))
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get products
    products, total = list_products(session, q=q, sort=sort, order=order, 
                                  limit=page_size, offset=offset)
    
    # Create pagination info
    pagination = create_pagination_info(total, page, page_size)
    
    # Build page URLs
    current_params = {"q": q, "sort": sort, "order": order, "page_size": page_size}
    pagination['page_urls'] = {
        p: build_page_urls("/products", current_params, p) 
        for p in pagination['page_range']
    }
    if pagination['has_previous']:
        pagination['previous_url'] = build_page_urls("/products", current_params, pagination['previous_page'])
    if pagination['has_next']:
        pagination['next_url'] = build_page_urls("/products", current_params, pagination['next_page'])
    
    return templates.TemplateResponse("products/index.html", {
        "request": request,
        "products": products,
        "pagination": pagination,
        "search_query": q,
        "sort": sort,
        "order": order
    })


# Import sub-routers
from .products_routes.crud import router as crud_router
from .products_routes.csv import router as csv_router

# Include sub-routers
router.include_router(crud_router)
router.include_router(csv_router)

