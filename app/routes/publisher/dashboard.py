"""Publisher dashboard routes."""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db import get_session
from app.repos.tenants import get_tenant_by_slug
from app.repos.products import list_products
from app.utils.env import get_service_base_url

router = APIRouter()
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
    
    # Compute MCP endpoint URL
    endpoint_url = f"{get_service_base_url()}/mcp/agents/{tenant_slug}/rpc"
    
    return templates.TemplateResponse("publisher/dashboard.html", {
        "request": request,
        "tenant": tenant,
        "product_count": total,
        "has_custom_prompt": has_custom_prompt,
        "endpoint_url": endpoint_url
    })
