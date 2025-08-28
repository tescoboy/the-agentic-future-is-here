"""
Tenant context management service for session-based tenant switching.
"""

import logging
from typing import Optional
from fastapi import Request, Response, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.repos.tenants import get_tenant_by_slug

logger = logging.getLogger(__name__)


def get_current_tenant(request: Request) -> Optional["Tenant"]:
    """Get the current tenant from request state."""
    return getattr(request.state, 'tenant', None)


def set_current_tenant(request: Request, response: Response, tenant_slug: str) -> None:
    """Set the current tenant in a secure cookie."""
    # Compute secure flag based on environment and request scheme
    secure = (not request.app.debug) or request.url.scheme == "https"
    
    response.set_cookie(
        key="tenant_slug",
        value=tenant_slug,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/"
    )


def clear_current_tenant(response: Response) -> None:
    """Clear the current tenant cookie."""
    response.delete_cookie(
        key="tenant_slug",
        path="/"
    )


def resolve_tenant(slug: str) -> Optional["Tenant"]:
    """Resolve tenant by slug (non-failing, for middleware)."""
    try:
        with next(get_session()) as db_session:
            return get_tenant_by_slug(db_session, slug)
    except Exception as e:
        logger.warning(f"Failed to resolve tenant '{slug}': {str(e)}")
        return None


def resolve_tenant_or_404(slug: str) -> "Tenant":
    """Resolve tenant by slug (failing, for routes)."""
    tenant = resolve_tenant(slug)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"tenant '{slug}' not found")
    return tenant
