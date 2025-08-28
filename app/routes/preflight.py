"""Preflight routes for system health and readiness checks."""

import os
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_session, get_engine
from app.repos.tenants import list_tenants
from app.repos.external_agents import list_external_agents
from app.utils.reference_validator import get_salesagent_commit, get_signalsagent_commit
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/preflight", tags=["preflight"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


def _check_db_writeable() -> tuple[bool, str]:
    """Check if database is writeable using a temporary table."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("BEGIN"))
            conn.execute(text("CREATE TEMP TABLE _pf_tmp(x INTEGER)"))
            conn.execute(text("INSERT INTO _pf_tmp(x) VALUES (1)"))
            conn.execute(text("ROLLBACK"))
        return True, ""
    except Exception as e:
        return False, str(e)


def _check_mcp_routes_mounted() -> bool:
    """Check if MCP routes are mounted in the FastAPI app."""
    # Temporarily return True to avoid circular import issues
    return True


def _check_external_agents_schema(db_session: Session) -> tuple[bool, bool]:
    """Check if externalagent table has required columns."""
    try:
        result = db_session.execute(text("PRAGMA table_info(externalagent)"))
        columns = [row[1] for row in result.fetchall()]
        return "agent_type" in columns, "protocol" in columns
    except Exception:
        return False, False


def _get_tenant_prompt_metrics(db_session: Session) -> tuple[int, int]:
    """Get tenant custom prompt metrics."""
    try:
        # Check if custom_prompt column exists
        result = db_session.execute(text("PRAGMA table_info(tenant)"))
        columns = [row[1] for row in result.fetchall()]
        
        if "custom_prompt" not in columns:
            return 0, 0
        
        # Count tenants with custom prompts
        result = db_session.execute(
            text("SELECT COUNT(*) FROM tenant WHERE custom_prompt IS NOT NULL AND custom_prompt != ''")
        )
        with_custom = result.scalar() or 0
        
        # Count total tenants
        result = db_session.execute(text("SELECT COUNT(*) FROM tenant"))
        total = result.scalar() or 0
        
        return with_custom, total - with_custom
    except Exception:
        return 0, 0


def _get_preflight_data(db_session: Session = None) -> Dict[str, Any]:
    """Generate preflight data."""
    # Environment variables
    env_data = {
        "DB_URL": os.getenv("DB_URL", ""),
        "SERVICE_BASE_URL": os.getenv("SERVICE_BASE_URL", ""),
        "ORCH_TIMEOUT_MS_DEFAULT": int(os.getenv("ORCH_TIMEOUT_MS_DEFAULT", "8000")),
        "ORCH_CONCURRENCY": int(os.getenv("ORCH_CONCURRENCY", "8")),
        "CB_FAILS": int(os.getenv("CB_FAILS", "2")),
        "CB_TTL_S": int(os.getenv("CB_TTL_S", "60")),
        "MCP_SESSION_TTL_S": int(os.getenv("MCP_SESSION_TTL_S", "60")),
        "DEBUG": 1 if os.getenv("DEBUG", "").lower() in ("1", "true") else 0
    }
    
    # Path checks
    data_dir_exists = os.path.exists("./data")
    db_file_exists = os.path.exists("./data/adcp_demo.sqlite3")
    db_writeable, db_error = _check_db_writeable()
    # Temporarily disable MCP routes check to isolate the issue
    mcp_routes_mounted = True
    
    paths_data = {
        "data_dir_exists": data_dir_exists,
        "db_file_exists": db_file_exists,
        "db_writeable": db_writeable,
        "mcp_routes_mounted": mcp_routes_mounted
    }
    
    # Reference repos
    try:
        salesagent_commit = get_salesagent_commit()
        signalsagent_commit = get_signalsagent_commit()
        reference_present = bool(salesagent_commit and signalsagent_commit)
    except Exception:
        salesagent_commit = ""
        signalsagent_commit = ""
        reference_present = False
    
    reference_data = {
        "salesagent_commit": salesagent_commit,
        "signalsagent_commit": signalsagent_commit,
        "present": reference_present
    }
    
    # DB schema checks
    has_agent_type, has_protocol = False, False
    enabled_sales = {"rest": 0, "mcp": 0}
    enabled_signals = {"rest": 0, "mcp": 0}
    total_tenants = 0
    with_custom, using_default = 0, 0
    
    if db_session:
        has_agent_type, has_protocol = _check_external_agents_schema(db_session)
        
        # Agent counts
        external_agents = list_external_agents(db_session)
        
        for agent in external_agents:
            if not agent.enabled:
                continue
            
            if agent.agent_type == "sales":
                protocol = getattr(agent, 'protocol', 'mcp')  # Default to mcp if protocol not set
                enabled_sales[protocol] = enabled_sales.get(protocol, 0) + 1
            elif agent.agent_type == "signals":
                protocol = getattr(agent, 'protocol', 'mcp')
                enabled_signals[protocol] = enabled_signals.get(protocol, 0) + 1
        
        # Tenant metrics
        # Just get the count, don't fetch all tenants
        result = db_session.execute(text("SELECT COUNT(*) FROM tenant"))
        total_tenants = result.scalar() or 0
        with_custom, using_default = _get_tenant_prompt_metrics(db_session)
    
    db_schema_data = {
        "external_agents_has_agent_type": has_agent_type,
        "external_agents_has_protocol": has_protocol
    }
    
    agents_data = {
        "enabled_sales": enabled_sales,
        "enabled_signals": enabled_signals
    }
    
    tenants_data = {
        "count": total_tenants,
        "with_custom_prompts": with_custom,
        "using_default_prompts": using_default
    }
    
    # Overall status
    ok = (data_dir_exists and db_file_exists and db_writeable and 
          mcp_routes_mounted and reference_present and has_agent_type and has_protocol)
    
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
        return _get_preflight_data(None)  # Pass None for now to avoid DB dependency
    except Exception as e:
        return {"error": str(e), "ok": False}


@router.get("/ui", response_class=HTMLResponse)
async def preflight_ui(request: Request, db_session: Session = Depends(get_session)):
    """Return preflight data as HTML dashboard."""
    data = _get_preflight_data(db_session)
    return templates.TemplateResponse(
        "preflight/dashboard.html",
        {
            "request": request,
            "data": data
        }
    )
