"""
Tenant middleware for reading tenant context from cookies.
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.services.tenant_context import resolve_tenant

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to read tenant_slug cookie and attach tenant to request state."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and attach tenant context if available."""
        # Read tenant_slug cookie
        tenant_slug = request.cookies.get("tenant_slug")
        
        if tenant_slug:
            # Resolve tenant (non-failing)
            tenant = resolve_tenant(tenant_slug)
            if tenant:
                request.state.tenant = tenant
                logger.debug(f"Attached tenant '{tenant_slug}' to request")
            else:
                logger.warning(f"Invalid tenant_slug in cookie: {tenant_slug}")
        
        # Continue processing
        response = await call_next(request)
        return response
