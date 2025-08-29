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

from app.db import ensure_database, create_all_tables, get_session
from app.models import Tenant, Product, ExternalAgent  # Import models to register them
from app.utils.migrations import run_migrations
from app.utils.reference_validator import validate_reference_repos
from app.utils.rag_migrations import run_rag_startup_checks
from app.routes import tenants, external_agents, products, mcp_rpc, buyer, tenant_switch, publisher, publishers
from app.routes.preflight import router as preflight_router
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


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        # 1. Validate reference repositories first (fail-fast) - skip in production
        logger.info("Skipping reference repository validation (production mode)")
        
        # 2. Ensure data directory exists
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        
        # 3. Create base tables
        create_all_tables()
        
        # 4. Run migrations
        run_migrations()
        
        # 5. Initialize database connection
        ensure_database()
        
        # 6. Run embeddings migrations
        try:
            from app.utils.embeddings_migrations import run_embeddings_migrations
            session = next(get_session())
            run_embeddings_migrations(session)
            logger.info("Embeddings migrations completed successfully")
        except Exception as e:
            logger.warning(f"Embeddings migrations failed: {e}")
        finally:
            if 'session' in locals():
                session.close()
        
        # 7. Run RAG startup checks (after database tables are created)
        try:
            session = next(get_session())
            # Check if product table exists before running RAG checks
            from sqlalchemy import text
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='product'"))
            if result.fetchone():
                run_rag_startup_checks(session)
                logger.info("RAG startup checks completed successfully")
            else:
                logger.warning("Product table not found, skipping RAG startup checks")
        except Exception as e:
            logger.warning(f"RAG startup checks failed (will retry later): {e}")
        finally:
            if 'session' in locals():
                session.close()
        
        # 8. Start embedding worker if enabled
        try:
            from app.services.embedding_queue import start_worker
            await start_worker(app)
        except Exception as e:
            logger.warning(f"Failed to start embedding worker: {e}")
        
    except Exception as e:
        # Log the error and re-raise to prevent startup
        logger.error(f"Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    try:
        # Shutdown embedding worker
        from app.services.embedding_queue import shutdown_worker
        await shutdown_worker()
        logger.info("Embedding worker shutdown completed")
    except Exception as e:
        logger.warning(f"Embedding worker shutdown failed: {e}")


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


@app.get("/test-rag/{tenant_slug}")
async def test_rag(tenant_slug: str, brief: str = "eco-conscious"):
    """Test RAG pre-filter functionality."""
    try:
        from app.repos.tenants import get_tenant_by_slug
        from app.services.product_rag import filter_products_for_brief
        from app.db import get_session
        
        session = next(get_session())
        tenant = get_tenant_by_slug(session, tenant_slug)
        if not tenant:
            return {"error": f"Tenant '{tenant_slug}' not found"}
        
        candidates = await filter_products_for_brief(session, tenant.id, brief, 5)
        
        return {
            "tenant": tenant_slug,
            "brief": brief,
            "candidates_count": len(candidates),
            "candidates": [{"product_id": c["product_id"], "name": c["name"], "score": c.get("rag_score", c.get("fts_score", 0))} for c in candidates[:3]]
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/test-env")
async def test_env():
    """Test environment variable availability."""
    import os
    from app.utils.env import get_gemini_api_key
    
    return {
        "GEMINI_API_KEY_in_os_environ": "GEMINI_API_KEY" in os.environ,
        "GEMINI_API_KEY_value": os.environ.get("GEMINI_API_KEY", "")[:10] + "..." if os.environ.get("GEMINI_API_KEY") else None,
        "get_gemini_api_key_available": get_gemini_api_key() is not None,
        "get_gemini_api_key_value": get_gemini_api_key()[:10] + "..." if get_gemini_api_key() else None
    }


@app.get("/debug/buyer/{tenant_slug}")
async def debug_buyer(tenant_slug: str):
    """Debug buyer flow for a specific tenant."""
    try:
        from app.repos.tenants import get_tenant_by_slug
        from app.repos.products import get_products_by_tenant
        from app.db import get_session
        
        session = next(get_session())
        
        # Check tenant exists
        tenant = get_tenant_by_slug(session, tenant_slug)
        if not tenant:
            return {"error": f"Tenant '{tenant_slug}' not found"}
        
        # Check products exist
        products, total = list_products(session, tenant_id=tenant.id)
        
        # Check external agents exist
        from app.repos.external_agents import list_external_agents
        agents = list_external_agents(session)
        
        return {
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug
            },
            "products_count": len(products),
            "agents_count": len(agents),
            "sample_products": [{"id": p.id, "name": p.name} for p in products[:3]],
            "sample_agents": [{"id": a.id, "name": a.name, "endpoint_url": a.endpoint_url} for a in agents[:3]]
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
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
