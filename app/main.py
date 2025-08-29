"""
AdCP Demo FastAPI application.
Main entry point for the FastAPI application.
"""

import logging
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.models import Tenant, Product, ExternalAgent  # Import models to register them
from app.routes import tenants, external_agents, products, mcp_rpc, buyer, tenant_switch, publisher, publishers
from app.routes.admin import backup
from app.routes.preflight import router as preflight_router
from app.middleware.tenant_middleware import TenantMiddleware
from app.startup import startup_event, shutdown_event
from app.endpoints import setup_endpoints

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="AdCP Demo",
    description="AdCP Demo with genuine MCP implementation",
    version="0.1.0"
)

# Configure templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Add tenant middleware
app.add_middleware(TenantMiddleware)

# Include routers
app.include_router(tenants.router)
app.include_router(products.router)
app.include_router(external_agents.router)
app.include_router(mcp_rpc.router)
app.include_router(buyer.router)
app.include_router(preflight_router)
app.include_router(tenant_switch.router)
app.include_router(publisher.router)
app.include_router(publishers.router)
app.include_router(backup.router)

# Setup endpoints and event handlers
setup_endpoints(app, templates)
app.on_event("startup")(startup_event)
app.on_event("shutdown")(shutdown_event)
