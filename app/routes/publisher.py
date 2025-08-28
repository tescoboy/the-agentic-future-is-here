"""Publisher routes for tenant-specific operations."""

import logging
from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from sqlalchemy import text

from app.db import get_session
from app.repos.tenants import get_tenant_by_slug
from app.repos.products import list_products, create_product, delete_product
from app.schemas import ProductForm
from app.services.sales_contract import get_default_sales_prompt
from app.utils.csv_utils import parse_csv_file, import_products_from_csv

router = APIRouter(prefix="/publisher", tags=["publisher"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


def _get_tenant_or_404(session: Session, tenant_slug: str):
    """Get tenant by slug or raise 404."""
    tenant = get_tenant_by_slug(session, tenant_slug)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"tenant '{tenant_slug}' not found")
    return tenant


@router.get("/{tenant_slug}/", response_class=HTMLResponse)
def publisher_dashboard(request: Request, tenant_slug: str, session: Session = Depends(get_session)):
    """Publisher dashboard for a specific tenant."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    # Get product count for this tenant
    products, total = list_products(session, tenant_id=tenant.id)
    
    # Check if custom prompt is set
    has_custom_prompt = bool(tenant.custom_prompt and tenant.custom_prompt.strip())
    
    return templates.TemplateResponse("publisher/dashboard.html", {
        "request": request,
        "tenant": tenant,
        "product_count": total,
        "has_custom_prompt": has_custom_prompt
    })


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
def publisher_create_product(request: Request, tenant_slug: str, session: Session = Depends(get_session),
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


@router.get("/{tenant_slug}/products/import", response_class=HTMLResponse)
def publisher_csv_import_form(request: Request, tenant_slug: str, session: Session = Depends(get_session)):
    """Publisher's CSV import form."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    return templates.TemplateResponse("publisher/import_form.html", {
        "request": request,
        "tenant": tenant,
        "show_form": True
    })


@router.post("/{tenant_slug}/products/import", response_class=HTMLResponse)
def publisher_csv_import_action(request: Request, tenant_slug: str, session: Session = Depends(get_session),
                              file: UploadFile = File(...)):
    """Import products from CSV for this publisher."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    # Validate file type
    if not file.content_type in ["text/csv", "application/vnd.ms-excel"]:
        return templates.TemplateResponse("publisher/import_form.html", {
            "request": request,
            "tenant": tenant,
            "show_form": False,
            "import_result": {
                "error": f"Invalid file type. Expected CSV, got {file.content_type}"
            }
        })
    
    # Validate file size (5MB limit)
    if file.size and file.size > 5 * 1024 * 1024:
        return templates.TemplateResponse("publisher/import_form.html", {
            "request": request,
            "tenant": tenant,
            "show_form": False,
            "import_result": {
                "error": "File too large. Maximum size is 5MB."
            }
        })
    
    try:
        # Read file content
        content = file.file.read()
        
        # Parse CSV (don't require tenant_slug for publisher imports)
        valid_rows, invalid_rows, parse_errors = parse_csv_file(content, require_tenant_slug=False)
        
        # Check if CSV has tenant column and warn
        tenant_column_warning = None
        if valid_rows and any('tenant' in row or 'tenant_id' in row for row in valid_rows):
            tenant_column_warning = f"Ignored tenant column in CSV. All rows were imported for '{tenant_slug}'."
        
        # Import valid rows under this tenant
        imported_count, import_errors = import_products_from_csv(session, valid_rows, tenant_id=tenant.id)
        
        # Combine all errors
        all_errors = parse_errors + import_errors
        
        return templates.TemplateResponse("publisher/import_form.html", {
            "request": request,
            "tenant": tenant,
            "show_form": False,
            "import_result": {
                "total_rows": len(valid_rows) + len(invalid_rows),
                "imported_count": imported_count,
                "invalid_count": len(invalid_rows) + len(all_errors),
                "errors": all_errors,
                "tenant_column_warning": tenant_column_warning
            }
        })
        
    except Exception as e:
        return templates.TemplateResponse("publisher/import_form.html", {
            "request": request,
            "tenant": tenant,
            "show_form": False,
            "import_result": {
                "error": f"Import failed: {str(e)}"
            }
        })


@router.get("/{tenant_slug}/prompt", response_class=HTMLResponse)
def publisher_prompt_form(request: Request, tenant_slug: str, session: Session = Depends(get_session)):
    """Publisher's custom prompt form."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    default_prompt = get_default_sales_prompt()
    
    return templates.TemplateResponse("publisher/prompt_form.html", {
        "request": request,
        "tenant": tenant,
        "default_prompt": default_prompt,
        "errors": {}
    })


@router.post("/{tenant_slug}/prompt", response_class=HTMLResponse)
def publisher_update_prompt(request: Request, tenant_slug: str, session: Session = Depends(get_session),
                          custom_prompt: str = Form("")):
    """Update publisher's custom prompt."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    errors = {}
    
    # Validate custom prompt length
    if len(custom_prompt) > 8000:
        errors["custom_prompt"] = "Custom prompt must be 8000 characters or less"
    
    if errors:
        default_prompt = get_default_sales_prompt()
        return templates.TemplateResponse("publisher/prompt_form.html", {
            "request": request,
            "tenant": tenant,
            "default_prompt": default_prompt,
            "errors": errors,
            "custom_prompt": custom_prompt
        })
    
    # Update tenant custom prompt (empty string becomes NULL)
    if custom_prompt.strip():
        tenant.custom_prompt = custom_prompt.strip()
        logger.info(f"Updated custom prompt for tenant {tenant_slug}")
    else:
        tenant.custom_prompt = None
        logger.info(f"Cleared custom prompt for tenant {tenant_slug}")
    
    session.add(tenant)
    session.commit()
    
    return RedirectResponse(url=f"/publisher/{tenant_slug}/", status_code=302)
