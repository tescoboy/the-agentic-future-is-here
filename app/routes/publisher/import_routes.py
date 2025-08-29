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
    """Show CSV import form for publisher."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    return templates.TemplateResponse("publisher/import_form.html", {
        "request": request,
        "tenant": tenant,
        "show_form": True
    })


@router.post("/{tenant_slug}/products/import", response_class=HTMLResponse)
def publisher_csv_import_action(request: Request, tenant_slug: str, session: Session = Depends(get_session),
                              file: UploadFile = File(...)):
    """Handle CSV import for publisher."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    try:
        # Parse CSV file
        parse_errors, valid_rows, invalid_rows = parse_csv_file(file)
        
        if parse_errors:
            return templates.TemplateResponse("publisher/import_form.html", {
                "request": request,
                "tenant": tenant,
                "show_form": False,
                "import_result": {
                    "error": f"CSV parsing failed: {parse_errors}"
                }
            })
        
        # Import products
        import_errors, imported_count, tenant_column_warning = import_products_from_csv(
            session, tenant.id, valid_rows
        )
        
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
def publisher_prompt_redirect(request: Request, tenant_slug: str, session: Session = Depends(get_session)):
    """Redirect publisher prompt management to admin route for single source of truth."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    # Redirect to admin prompt management
    return RedirectResponse(url=f"/tenants/{tenant.id}/prompt", status_code=302)


@router.post("/{tenant_slug}/prompt", response_class=HTMLResponse)
def publisher_prompt_redirect_post(request: Request, tenant_slug: str, session: Session = Depends(get_session)):
    """Redirect POST requests to admin route for single source of truth."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    # Redirect to admin prompt management
    return RedirectResponse(url=f"/tenants/{tenant.id}/prompt", status_code=302)
