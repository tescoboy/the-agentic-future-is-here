"""Tenant prompt management routes."""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db import get_session
from app.repos.tenants import get_tenant_by_id
from app.services.sales_contract import get_default_sales_prompt

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/{tenant_id}/prompt")
def prompt_admin_form(request: Request, tenant_id: int, session: Session = Depends(get_session)):
    """Show prompt admin form."""
    tenant = get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    default_prompt = get_default_sales_prompt()
    
    return templates.TemplateResponse("tenants/prompt.html", {
        "request": request,
        "tenant": tenant,
        "default_prompt": default_prompt,
        "custom_prompt": tenant.custom_prompt or "",  # Add this line to fix the issue
        "errors": {}
    })


@router.post("/{tenant_id}/prompt")
def update_prompt_action(request: Request, tenant_id: int, session: Session = Depends(get_session),
                        custom_prompt: str = Form("")):
    """Update tenant custom prompt."""
    tenant = get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    errors = {}
    
    # Validate custom prompt length
    if len(custom_prompt) > 8000:
        errors["custom_prompt"] = "Custom prompt must be 8000 characters or less"
    
    if errors:
        default_prompt = get_default_sales_prompt()
        return templates.TemplateResponse("tenants/prompt.html", {
            "request": request,
            "tenant": tenant,
            "default_prompt": default_prompt,
            "errors": errors,
            "custom_prompt": custom_prompt  # Preserve content on validation error
        })
    
    # Update tenant custom prompt (empty string becomes NULL)
    if custom_prompt.strip():
        tenant.custom_prompt = custom_prompt.strip()
    else:
        tenant.custom_prompt = None
    
    session.add(tenant)
    session.commit()
    
    return RedirectResponse(url="/tenants", status_code=302)
