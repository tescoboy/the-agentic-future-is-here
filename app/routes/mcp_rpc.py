"""MCP JSON-RPC server routes for Sales agents."""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from sqlmodel import Session
from typing import Optional

from app.db import get_session
from app.repos.tenants import list_tenants
from app.services.mcp_session import session_store
from app.services.mcp_rpc_handlers import dispatch, validate_json_rpc_envelope, MCPRPCError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/")
def get_server_info():
    """Get MCP server metadata."""
    return {
        "service": "adcp-sales",
        "version": "0.1.0",
        "description": "AdCP Sales Agent MCP Server"
    }


@router.post("/agents/{tenant_slug}/rpc")
async def handle_json_rpc(
    request: Request,
    tenant_slug: str,
    db_session: Session = Depends(get_session),
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id")
):
    """Handle JSON-RPC requests for a specific tenant."""
    try:
        # Parse JSON-RPC request
        data = await request.json()
        validate_json_rpc_envelope(data)
        
        method = data["method"]
        params = data["params"]
        request_id = data["id"]
        
        # Check if this is a follow-up request requiring session
        if method not in ["mcp.get_info", "initialize"]:
            if mcp_session_id:
                # Validate session
                session_tenant = session_store.validate_session(mcp_session_id)
                if not session_tenant or session_tenant != tenant_slug:
                    raise MCPRPCError(-32000, "session invalid or expired")
            else:
                # Check if a session already exists for this tenant
                if session_store.has_session_for_tenant(tenant_slug):
                    raise MCPRPCError(-32000, "session required")
        
        # Dispatch the method
        result = await dispatch(method, params, tenant_slug, db_session)
        
        # Create response
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
        # Create session on initialize or first successful call (except get_info)
        if method == "initialize" or (method not in ["mcp.get_info", "notifications/initialized"] and not mcp_session_id):
            session_id = session_store.create_session(tenant_slug)
            response_obj = JSONResponse(content=response)
            response_obj.headers["Mcp-Session-Id"] = session_id
            return response_obj
        
        logger.info(f"rpc method={method} id={request_id} keys=result")
        return response
        
    except MCPRPCError as e:
        # JSON-RPC error response
        error_response = {
            "jsonrpc": "2.0",
            "id": data.get("id") if 'data' in locals() else None,
            "error": {
                "code": e.code,
                "message": e.message
            }
        }
        logger.info(f"rpc method={data.get('method', 'unknown')} id={data.get('id', 'unknown')} keys=error")
        return JSONResponse(content=error_response, status_code=200)
    
    except Exception as e:
        # Generic server error
        error_response = {
            "jsonrpc": "2.0",
            "id": data.get("id") if 'data' in locals() else None,
            "error": {
                "code": -32000,
                "message": "internal server error"
            }
        }
        logger.error(f"Unexpected error in JSON-RPC: {str(e)}")
        return JSONResponse(content=error_response, status_code=200)


@router.delete("/agents/{tenant_slug}/rpc")
async def delete_session(
    tenant_slug: str,
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id")
):
    """Delete MCP session."""
    if mcp_session_id:
        session_store.delete_session(mcp_session_id)
    return {"ok": True}


@router.post("/agents/{tenant_slug}/rank")
async def rest_rank_products(
    request: Request,
    tenant_slug: str,
    db_session: Session = Depends(get_session)
):
    """REST shim for rank_products method."""
    try:
        # Parse request body
        data = await request.json()
        brief = data.get("brief")
        
        if not brief or not isinstance(brief, str) or not brief.strip():
            raise HTTPException(status_code=400, detail="brief must be a non-empty string")
        
        # Call the MCP handler directly
        params = {"brief": brief}
        result = dispatch("rank_products", params, tenant_slug, db_session)
        
        # Return result object (not JSON-RPC envelope)
        return result
        
    except MCPRPCError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Error in REST rank endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="internal server error")
