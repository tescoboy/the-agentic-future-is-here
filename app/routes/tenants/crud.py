"""Tenant CRUD routes."""

import logging
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db import get_session
from app.schemas import TenantForm
from app.repos.tenants import (
    create_tenant, get_tenant_by_id, list_tenants, 
    update_tenant, delete_tenant, bulk_delete_all_tenants
)
from app.utils.pagination import create_pagination_info, build_page_urls

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def list_tenants_view(request: Request, session: Session = Depends(get_session),
                     q: str = "", page: int = 1, page_size: int = 20):
    """List tenants with search and pagination."""
    # Clamp page_size
    page_size = max(1, min(page_size, 100))
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get tenants
    tenants, total = list_tenants(session, q=q, limit=page_size, offset=offset)
    
    # Create pagination info
    pagination = create_pagination_info(total, page, page_size)
    
    # Build page URLs
    current_params = {"q": q, "page_size": page_size}
    pagination['page_urls'] = {
        p: build_page_urls("/tenants", current_params, p) 
        for p in pagination['page_range']
    }
    if pagination['has_previous']:
        pagination['previous_url'] = build_page_urls("/tenants", current_params, pagination['previous_page'])
    if pagination['has_next']:
        pagination['next_url'] = build_page_urls("/tenants", current_params, pagination['next_page'])
    
    return templates.TemplateResponse("tenants/index.html", {
        "request": request,
        "tenants": tenants,
        "pagination": pagination,
        "search_query": q
    })


@router.get("/new")
def new_tenant_form(request: Request):
    """Show new tenant form."""
    return templates.TemplateResponse("tenants/form.html", {
        "request": request,
        "errors": {}
    })


@router.post("/")
def create_tenant_action(request: Request, session: Session = Depends(get_session),
                        name: str = Form(...), slug: str = Form(...)):
    """Create a new tenant."""
    try:
        form = TenantForm(name=name, slug=slug)
        tenant = create_tenant(session, form.name, form.slug)
        return RedirectResponse(url="/tenants", status_code=302)
    except Exception as e:
        return templates.TemplateResponse("tenants/form.html", {
            "request": request,
            "errors": {"form": str(e)},
            "name": name,
            "slug": slug
        })


@router.get("/{tenant_id}/edit")
def edit_tenant_form(request: Request, tenant_id: int, session: Session = Depends(get_session)):
    """Show edit tenant form."""
    tenant = get_tenant_by_id(session, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return templates.TemplateResponse("tenants/form.html", {
        "request": request, 
        "tenant": tenant,
        "errors": {}
    })


@router.post("/{tenant_id}/edit")
def update_tenant_action(request: Request, tenant_id: int, session: Session = Depends(get_session),
                        name: str = Form(...), slug: str = Form(...)):
    """Update a tenant."""
    try:
        form = TenantForm(name=name, slug=slug)
        tenant = update_tenant(session, tenant_id, form.name, form.slug)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return RedirectResponse(url="/tenants", status_code=302)
    except Exception as e:
        tenant = get_tenant_by_id(session, tenant_id)
        return templates.TemplateResponse("tenants/form.html", {
            "request": request,
            "tenant": tenant,
            "errors": {"form": str(e)},
            "name": name,
            "slug": slug
        })


@router.post("/delete-all")
def bulk_delete_all_tenants_action(session: Session = Depends(get_session)):
    """Delete all tenants."""
    try:
        deleted_count = bulk_delete_all_tenants(session)
        return RedirectResponse(url="/tenants", status_code=302)
    except Exception as e:
        # Log the error and re-raise
        logger.error(f"Error in bulk delete: {e}")
        raise


@router.post("/{tenant_id}/delete")
def delete_tenant_action(tenant_id: int, session: Session = Depends(get_session)):
    """Delete a tenant."""
    success = delete_tenant(session, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return RedirectResponse(url="/tenants", status_code=302)
