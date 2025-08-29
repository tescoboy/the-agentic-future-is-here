"""Preflight route endpoints."""

import os
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.routes.preflight.checks import check_paths, check_external_agents_schema
from app.routes.preflight.metrics import (
    get_tenant_prompt_metrics, get_agent_metrics, 
    get_reference_data, get_tenant_count
)
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


def get_preflight_data(db_session: Session = None) -> Dict[str, Any]:
    """Generate preflight data."""
    # Environment variables
    env_data = {
        "DB_URL": os.getenv("DB_URL", ""),
        "SERVICE_BASE_URL": os.getenv("SERVICE_BASE_URL", ""),
        "ORCH_TIMEOUT_MS_DEFAULT": int(os.getenv("ORCH_TIMEOUT_MS_DEFAULT", "25000")),
        "ORCH_CONCURRENCY": int(os.getenv("ORCH_CONCURRENCY", "8")),
        "CB_FAILS": int(os.getenv("CB_FAILS", "2")),
        "CB_TTL_S": int(os.getenv("CB_TTL_S", "60")),
        "MCP_SESSION_TTL_S": int(os.getenv("MCP_SESSION_TTL_S", "60")),
        "DEBUG": 1 if os.getenv("DEBUG", "").lower() in ("1", "true") else 0
    }
    
    # Path checks
    paths_data = check_paths()
    
    # Reference repos
    reference_data = get_reference_data()
    
    # DB schema checks
    has_agent_type, has_protocol = False, False
    agents_data = {"enabled_sales": {"rest": 0, "mcp": 0}, "enabled_signals": {"rest": 0, "mcp": 0}}
    total_tenants = 0
    with_custom, using_default = 0, 0
    
    if db_session:
        has_agent_type, has_protocol = check_external_agents_schema(db_session)
        agents_data = get_agent_metrics(db_session)
        total_tenants = get_tenant_count(db_session)
        with_custom, using_default = get_tenant_prompt_metrics(db_session)
    
    db_schema_data = {
        "external_agents_has_agent_type": has_agent_type,
        "external_agents_has_protocol": has_protocol
    }
    
    tenants_data = {
        "count": total_tenants,
        "with_custom_prompts": with_custom,
        "using_default_prompts": using_default
    }
    
    # Overall status
    ok = (paths_data["data_dir_exists"] and paths_data["db_file_exists"] and 
          paths_data["db_writeable"] and paths_data["mcp_routes_mounted"] and 
          reference_data["present"] and has_agent_type and has_protocol)
    
    return {
        "ok": ok,
        "service": "adcp-demo",
        "version": "0.1.0",
        "env": env_data,
        "paths": paths_data,
        "reference": reference_data,
        "db_schema": db_schema_data,
        "agents": agents_data,
        "tenants": tenants_data
    }


@router.get("/test", response_class=JSONResponse)
async def preflight_test():
    """Test endpoint."""
    return {"test": "ok", "ok": True}


@router.get("/status", response_class=JSONResponse)
async def preflight_json():
    """Return preflight data as JSON."""
    try:
        return get_preflight_data(None)
    except Exception as e:
        return {"error": str(e), "ok": False}


@router.get("/ui", response_class=HTMLResponse)
async def preflight_ui(request: Request, db_session: Session = Depends(get_session)):
    """Return preflight data as HTML dashboard."""
    data = get_preflight_data(db_session)
    return templates.TemplateResponse(
        "preflight/dashboard.html",
        {
            "request": request,
            "data": data
        }
    )

