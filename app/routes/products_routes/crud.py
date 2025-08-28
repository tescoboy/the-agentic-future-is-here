"""Product CRUD operations."""

from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db import get_session
from app.schemas import ProductForm
from app.repos.tenants import list_tenants
from app.repos.products import (
    create_product, get_product_by_id, update_product, delete_product
)
from app.services.tenant_context import get_current_tenant

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/new")
def new_product_form(request: Request, session: Session = Depends(get_session)):
    """Show new product form."""
    tenants, _ = list_tenants(session)
    return templates.TemplateResponse("products/form.html", {"request": request, "tenants": tenants})


@router.post("/")
def create_product_action(request: Request, session: Session = Depends(get_session),
                         tenant_id: int = Form(...), name: str = Form(...),
                         description: str = Form(""), price_cpm: float = Form(...),
                         delivery_type: str = Form(...), formats_json: str = Form("{}"),
                         targeting_json: str = Form("{}")):
    """Create a new product."""
    # Check tenant context if set
    current_tenant = get_current_tenant(request)
    if current_tenant and tenant_id != current_tenant.id:
        tenants, _ = list_tenants(session)
        return templates.TemplateResponse("products/form.html", {
            "request": request,
            "tenants": tenants,
            "errors": {"form": f"Tenant mismatch: form specifies tenant {tenant_id} but current context is tenant {current_tenant.id}"},
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
            tenant_id=tenant_id, name=name, description=description,
            price_cpm=price_cpm, delivery_type=delivery_type,
            formats_json=formats_json, targeting_json=targeting_json
        )
        product = create_product(
            session, form.tenant_id, form.name, form.description,
            form.price_cpm, form.delivery_type, form.formats_json, form.targeting_json
        )
        return RedirectResponse(url="/products", status_code=302)
    except Exception as e:
        tenants, _ = list_tenants(session)
        return templates.TemplateResponse("products/form.html", {
            "request": request,
            "tenants": tenants,
            "errors": {"form": str(e)},
            "tenant_id": tenant_id,
            "name": name,
            "description": description,
            "price_cpm": price_cpm,
            "delivery_type": delivery_type,
            "formats_json": formats_json,
            "targeting_json": targeting_json
        })


@router.get("/{product_id}/edit")
def edit_product_form(request: Request, product_id: int, session: Session = Depends(get_session)):
    """Show edit product form."""
    product = get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    tenants, _ = list_tenants(session)
    return templates.TemplateResponse("products/form.html", {
        "request": request, 
        "product": product, 
        "tenants": tenants,
        "errors": {}
    })


@router.post("/{product_id}/edit")
def update_product_action(request: Request, product_id: int, session: Session = Depends(get_session),
                         tenant_id: int = Form(...), name: str = Form(...),
                         description: str = Form(""), price_cpm: float = Form(...),
                         delivery_type: str = Form(...), formats_json: str = Form("{}"),
                         targeting_json: str = Form("{}")):
    """Update a product."""
    # Check tenant context if set
    current_tenant = get_current_tenant(request)
    if current_tenant and tenant_id != current_tenant.id:
        tenants, _ = list_tenants(session)
        product = get_product_by_id(session, product_id)
        return templates.TemplateResponse("products/form.html", {
            "request": request,
            "product": product,
            "tenants": tenants,
            "errors": {"form": f"Tenant mismatch: form specifies tenant {tenant_id} but current context is tenant {current_tenant.id}"},
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
            tenant_id=tenant_id, name=name, description=description,
            price_cpm=price_cpm, delivery_type=delivery_type,
            formats_json=formats_json, targeting_json=targeting_json
        )
        product = update_product(
            session, product_id, form.tenant_id, form.name, form.description,
            form.price_cpm, form.delivery_type, form.formats_json, form.targeting_json
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return RedirectResponse(url="/products", status_code=302)
    except Exception as e:
        product = get_product_by_id(session, product_id)
        tenants, _ = list_tenants(session)
        return templates.TemplateResponse("products/form.html", {
            "request": request,
            "product": product,
            "tenants": tenants,
            "errors": {"form": str(e)},
            "tenant_id": tenant_id,
            "name": name,
            "description": description,
            "price_cpm": price_cpm,
            "delivery_type": delivery_type,
            "formats_json": formats_json,
            "targeting_json": targeting_json
        })


@router.post("/{product_id}/delete")
def delete_product_action(product_id: int, session: Session = Depends(get_session)):
    """Delete a product."""
    success = delete_product(session, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return RedirectResponse(url="/products", status_code=302)
