"""Publisher dashboard routes."""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db import get_session
from app.repos.tenants import get_tenant_by_slug, update_tenant_web_context
from app.repos.products import list_products
from app.services.sales_contract import get_default_sales_prompt
from app.utils.env import get_service_base_url, get_web_grounding_config

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
    
    # Get web grounding configuration
    web_config = get_web_grounding_config()
    
    return templates.TemplateResponse("publisher/dashboard.html", {
        "request": request,
        "tenant": tenant,
        "product_count": total,
        "has_custom_prompt": has_custom_prompt,
        "endpoint_url": endpoint_url,
        "web_config": web_config
    })


@router.post("/{tenant_slug}/ai-enrichment", response_class=HTMLResponse)
def update_ai_enrichment_settings(
    request: Request, 
    tenant_slug: str, 
    enable_web_context: bool = Form(False),
    web_grounding_prompt: str = Form(None),
    custom_prompt: str = Form(None),
    session: Session = Depends(get_session)
):
    """Update AI enrichment settings for a tenant."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    try:
        # Update tenant with new web context setting
        update_tenant_web_context(session, tenant.id, enable_web_context)
        
        # Update web grounding prompt
        if web_grounding_prompt is not None:
            tenant.web_grounding_prompt = web_grounding_prompt.strip() if web_grounding_prompt.strip() else None
        
        # Update custom sales agent prompt
        if custom_prompt is not None:
            tenant.custom_prompt = custom_prompt.strip() if custom_prompt.strip() else None
        
        # Save all changes
        session.add(tenant)
        session.commit()
        
        # Redirect back to dashboard with success message
        response = RedirectResponse(url=f"/publisher/{tenant_slug}/", status_code=302)
        response.headers["Set-Cookie"] = "success_message=AI prompt settings updated successfully; Path=/; Max-Age=5"
        return response
        
    except Exception as e:
        logger.error(f"Failed to update AI enrichment settings for tenant {tenant_slug}: {str(e)}")
        response = RedirectResponse(url=f"/publisher/{tenant_slug}/", status_code=302)
        response.headers["Set-Cookie"] = "error_message=Failed to update AI prompt settings; Path=/; Max-Age=5"
        return response


@router.get("/{tenant_slug}/prompts", response_class=HTMLResponse)
def prompts_page(request: Request, tenant_slug: str, session: Session = Depends(get_session)):
    """Display the prompts management page."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    # Get web grounding configuration
    web_config = get_web_grounding_config()
    
    # Get default prompts
    default_sales_prompt = get_default_sales_prompt()
    
    # Default web grounding prompt
    default_web_grounding_prompt = """You are a consultant working for {tenant_name}. Your task is enriching an advertising campaign brief with fresh, web-sourced context. 

Focus on products from {tenant_name}'s catalogue (shows, actors, genres, or packages) 
and gather concise snippets that will help an advertiser understand why {tenant_name} inventory is a strong fit for the brief. This will help sales people promote the products to advertsiers.

Campaign Brief:
{brief}

{tenant_name} Products to Research:
{product_catalog}

Instructions:
1. Search for up-to-date information on each {tenant_name} products. 

2. Extract **short, factual snippets** (≤350 characters each) that describe that is relavent to the breif and advertiser:
   - The  audience, cultural relevance, or themes
   - Recent popularity, awards, or positive press coverage
   - Key actors, storylines, or events 
3. Write snippets that can be directly used to justify why a product aligns with the advertiser's brief.
4. Do not invent information. Only include details from real search results.
5. Return plain snippets, no formatting.

Response format:
{
  "snippets": [
    "Snippet 1 here…",
    "Snippet 2 here…"
  ]
}"""
    
    return templates.TemplateResponse("publisher/prompts.html", {
        "request": request,
        "tenant": tenant,
        "web_config": web_config,
        "default_sales_prompt": default_sales_prompt,
        "default_web_grounding_prompt": default_web_grounding_prompt
    })


@router.post("/{tenant_slug}/prompts", response_class=HTMLResponse)
def update_prompts(
    request: Request, 
    tenant_slug: str, 
    enable_web_context: bool = Form(False),
    web_grounding_prompt: str = Form(None),
    custom_prompt: str = Form(None),
    session: Session = Depends(get_session)
):
    """Update prompts and web grounding settings for a tenant."""
    tenant = _get_tenant_or_404(session, tenant_slug)
    
    try:
        # Update tenant with new web context setting
        update_tenant_web_context(session, tenant.id, enable_web_context)
        
        # Update web grounding prompt
        if web_grounding_prompt is not None:
            tenant.web_grounding_prompt = web_grounding_prompt.strip() if web_grounding_prompt.strip() else None
        
        # Update custom sales agent prompt
        if custom_prompt is not None:
            tenant.custom_prompt = custom_prompt.strip() if custom_prompt.strip() else None
        
        # Save all changes
        session.add(tenant)
        session.commit()
        
        # Redirect back to prompts page with success message
        response = RedirectResponse(url=f"/publisher/{tenant_slug}/prompts", status_code=302)
        response.headers["Set-Cookie"] = "success_message=AI prompts updated successfully; Path=/; Max-Age=5"
        return response
        
    except Exception as e:
        logger.error(f"Failed to update prompts for tenant {tenant_slug}: {str(e)}")
        response = RedirectResponse(url=f"/publisher/{tenant_slug}/prompts", status_code=302)
        response.headers["Set-Cookie"] = "error_message=Failed to update prompts; Path=/; Max-Age=5"
        return response
