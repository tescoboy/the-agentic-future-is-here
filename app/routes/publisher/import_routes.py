"""Publisher import and prompt routes."""

import logging
from fastapi import APIRouter, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db import get_session
from app.repos.tenants import get_tenant_by_slug
from app.services.sales_contract import get_default_sales_prompt
from app.utils.csv_utils import parse_csv_file, import_products_from_csv

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


def _get_tenant_or_404(session: Session, tenant_slug: str):
    """Get tenant by slug or raise 404."""
    tenant = get_tenant_by_slug(session, tenant_slug)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"tenant '{tenant_slug}' not found")
    return tenant


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
        
        # Queue embeddings for imported products if enabled
        enqueued_count = 0
        try:
            from app.utils.embeddings_config import is_embeddings_enabled
            from app.services.embedding_queue import get_embedding_queue
            
            if is_embeddings_enabled() and imported_count > 0:
                # Get the IDs of newly imported products
                from app.models import Product
                imported_products = session.query(Product).filter(
                    Product.tenant_id == tenant.id
                ).order_by(Product.id.desc()).limit(imported_count).all()
                
                if imported_products:
                    product_ids = [p.id for p in imported_products]
                    queue = get_embedding_queue()
                    enqueued_count = queue.enqueue_product_ids(product_ids)
                    logger.info(f"Queued {enqueued_count} imported products for embedding")
        except Exception as e:
            logger.warning(f"Failed to queue embeddings for imported products: {e}")
        
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
                "tenant_column_warning": tenant_column_warning,
                "enqueued_count": enqueued_count
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
