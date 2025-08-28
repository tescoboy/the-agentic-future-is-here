"""
AdCP Demo FastAPI application.
Main entry point with health endpoint and database initialization.
"""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

from app.db import ensure_database, create_all_tables
from app.utils.migrations import run_migrations
from app.utils.reference_validator import validate_reference_repos
from app.routes import tenants, external_agents, products, mcp_rpc, buyer, preflight, tenant_switch, publisher, publishers
from app.middleware.tenant_middleware import TenantMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="AdCP Demo",
    description="AdCP Demo with genuine MCP implementation",
    version="0.1.0"
)

# Add tenant middleware
app.add_middleware(TenantMiddleware)

# Configure templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(tenants.router)
app.include_router(products.router)
app.include_router(external_agents.router)
app.include_router(mcp_rpc.router)
app.include_router(buyer.router)
app.include_router(preflight.router)
app.include_router(tenant_switch.router)
app.include_router(publisher.router)
app.include_router(publishers.router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        # 1. Validate reference repositories first (fail-fast)
        repo_hashes = validate_reference_repos()
        logger.info(f"Reference repos: salesagent=<{repo_hashes['salesagent']}>, signals-agent=<{repo_hashes['signals-agent']}>")
        
        # 2. Ensure data directory exists
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        
        # 3. Create base tables
        create_all_tables()
        
        # 4. Run migrations
        run_migrations()
        
        # 5. Initialize database connection
        ensure_database()
        
    except Exception as e:
        # Log the error and re-raise to prevent startup
        logger.error(f"Startup failed: {str(e)}")
        raise


@app.get("/")
def root(request: Request):
    """Root endpoint redirects to products."""
    return templates.TemplateResponse("base.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and deployment verification."""
    return {
        "ok": True,
        "service": "adcp-demo"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Basic global exception handler for actionable error messages."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if str(exc) else "An unexpected error occurred"
        }
    )
