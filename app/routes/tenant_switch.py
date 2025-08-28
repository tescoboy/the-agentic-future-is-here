"""
Tenant switching routes for session-based tenant context.
"""

import logging
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.db import get_session
from app.repos.tenants import list_tenants
from app.services.tenant_context import set_current_tenant, clear_current_tenant, resolve_tenant_or_404
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/switch-tenant", tags=["tenant-switch"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def switch_tenant_form(request: Request, session: Session = Depends(get_session)):
    """Show tenant switching form."""
    tenants, _ = list_tenants(session)
    return templates.TemplateResponse("tenant_switch/index.html", {
        "request": request,
        "tenants": tenants
    })


@router.post("/")
async def switch_tenant(request: Request, session: Session = Depends(get_session)):
    """Switch to a specific tenant."""
    form_data = await request.form()
    tenant_slug = form_data.get("tenant_slug")
    
    if not tenant_slug:
        raise HTTPException(status_code=400, detail="tenant_slug is required")
    
    # Validate tenant exists
    tenant = resolve_tenant_or_404(tenant_slug)
    
    logger.info(f"Switched to tenant: {tenant_slug}")
    
    # Create redirect response with cookie
    response = RedirectResponse(url="/buyer", status_code=302)
    set_current_tenant(request, response, tenant_slug)
    
    return response


@router.post("/clear")
def clear_tenant_context(request: Request):
    """Clear current tenant context."""
    logger.info("Cleared tenant context")
    
    # Create redirect response with cookie cleared
    response = RedirectResponse(url="/switch-tenant", status_code=302)
    clear_current_tenant(response)
    
    return response
