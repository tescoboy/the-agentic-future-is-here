"""Publisher product management routes."""

import logging
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from sqlalchemy import text

from app.db import get_session
from app.repos.tenants import get_tenant_by_slug
from app.repos.products import list_products, create_product
from app.schemas import ProductForm

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


def _get_tenant_or_404(session: Session, tenant_slug: str):
    """Get tenant by slug or raise 404."""
    tenant = get_tenant_by_slug(session, tenant_slug)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"tenant '{tenant_slug}' not found")
    return tenant


@router.get("/{tenant_slug}/products", response_class=HTMLResponse)
def publisher_products(request: Request, tenant_slug: str, session: Session = Depends(get_session),
                      q: str = "", sort: str = "created_at", order: str = "desc",
                      page: int = 1, page_size: int = 20):
    """Publisher's products page."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    # Clamp page_size
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size
    
    # Get products for this tenant only
    products, total = list_products(session, q=q, sort=sort, order=order, 
                                  limit=page_size, offset=offset, tenant_id=tenant.id)
    
    # Create pagination info
    from app.utils.pagination import create_pagination_info, build_page_urls
    pagination = create_pagination_info(total, page, page_size)
    
    # Build page URLs
    current_params = {"q": q, "sort": sort, "order": order, "page_size": page_size}
    pagination['page_urls'] = {
        p: build_page_urls(f"/publisher/{tenant_slug}/products", current_params, p) 
        for p in pagination['page_range']
    }
    if pagination['has_previous']:
        pagination['previous_url'] = build_page_urls(f"/publisher/{tenant_slug}/products", current_params, pagination['previous_page'])
    if pagination['has_next']:
        pagination['next_url'] = build_page_urls(f"/publisher/{tenant_slug}/products", current_params, pagination['next_page'])
    
    return templates.TemplateResponse("publisher/products_index.html", {
        "request": request,
        "tenant": tenant,
        "products": products,
        "pagination": pagination,
        "search_query": q,
        "sort": sort,
        "order": order
    })


@router.get("/{tenant_slug}/products/new", response_class=HTMLResponse)
def publisher_new_product_form(request: Request, tenant_slug: str, session: Session = Depends(get_session)):
    """Publisher's new product form."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    return templates.TemplateResponse("publisher/products_form.html", {
        "request": request,
        "tenant": tenant,
        "errors": {}
    })


@router.post("/{tenant_slug}/products", response_class=HTMLResponse)
async def publisher_create_product(request: Request, tenant_slug: str, session: Session = Depends(get_session),
                           tenant_id: int = Form(...), name: str = Form(...),
                           description: str = Form(""), price_cpm: float = Form(...),
                           delivery_type: str = Form(...), formats_json: str = Form("{}"),
                           targeting_json: str = Form("{}")):
    """Create product under publisher tenant."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    # Check for tenant mismatch
    if tenant_id != tenant.id:
        return templates.TemplateResponse("publisher/products_form.html", {
            "request": request,
            "tenant": tenant,
            "errors": {"form": f"Tenant mismatch: form specifies tenant \"{tenant_id}\" but current context is \"{tenant_slug}\"."},
            "tenant_id": tenant_id,
            "name": name,
            "description": description,
            "price_cpm": price_cpm,
            "delivery_type": delivery_type,
            "formats_json": formats_json,
            "targeting_json": targeting_json
        })
    
    try:
        form = ProductForm(
            tenant_id=tenant.id, name=name, description=description,
            price_cpm=price_cpm, delivery_type=delivery_type,
            formats_json=formats_json, targeting_json=targeting_json
        )
        product = create_product(
            session, form.tenant_id, form.name, form.description,
            form.price_cpm, form.delivery_type, form.formats_json, form.targeting_json
        )
        
        # Queue embedding if enabled
        try:
            from app.utils.embeddings_config import is_embeddings_enabled
            from app.services.embedding_queue import get_embedding_queue
            
            if is_embeddings_enabled():
                queue = get_embedding_queue()
                enqueued = queue.enqueue_product_ids([product.id])
                if enqueued > 0:
                    logger.info(f"Queued product {product.id} for embedding")
        except Exception as e:
            logger.warning(f"Failed to queue embedding for product {product.id}: {e}")
        
        return RedirectResponse(url=f"/publisher/{tenant_slug}/products", status_code=302)
    except Exception as e:
        return templates.TemplateResponse("publisher/products_form.html", {
            "request": request,
            "tenant": tenant,
            "errors": {"form": str(e)},
            "tenant_id": tenant_id,
            "name": name,
            "description": description,
            "price_cpm": price_cpm,
            "delivery_type": delivery_type,
            "formats_json": formats_json,
            "targeting_json": targeting_json
        })


@router.post("/{tenant_slug}/products/delete-all", response_class=HTMLResponse)
def publisher_delete_all_products(request: Request, tenant_slug: str, session: Session = Depends(get_session)):
    """Delete all products for this publisher."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    try:
        # Delete all products for this tenant
        result = session.execute(
            text("DELETE FROM product WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant.id}
        )
        session.commit()
        
        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} products for tenant {tenant_slug}")
        
        return RedirectResponse(url=f"/publisher/{tenant_slug}/products", status_code=302)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to delete products for tenant {tenant_slug}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete products")
