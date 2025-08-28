"""
Helper functions for MCP client operations.
"""

import logging
from typing import Dict, Any
import httpx

from .mcp_errors import MCPHTTPError, MCPRPCError

logger = logging.getLogger(__name__)


def build_init_payload(request_id: int) -> Dict[str, Any]:
    """Build MCP initialize payload."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {"name": "adcp-demo", "version": "0.1.0"}
        }
    }


def build_rpc_payload(request_id: int, method: str, params: Dict) -> Dict[str, Any]:
    """Build MCP RPC payload."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }


def build_notification_payload() -> Dict[str, Any]:
    """Build MCP notification payload."""
    return {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }


def get_standard_headers(session_id: str = None) -> Dict[str, str]:
    """Get standard headers for MCP requests."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "adcp-demo/0.1.0"
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    return headers


def handle_http_response(response: httpx.Response, request_id: int, base_url: str) -> Dict[str, Any]:
    """Handle HTTP response and extract JSON-RPC data."""
    # Handle HTTP errors
    if response.status_code < 200 or response.status_code >= 300:
        body_preview = response.text[:200] if response.text else ""
        raise MCPHTTPError(response.status_code, "POST", base_url, body_preview)
    
    # Parse JSON-RPC response
    try:
        data = response.json()
    except Exception:
        raise MCPRPCError(-32000, "invalid JSON-RPC response: not valid JSON", request_id)
    
    # Handle RPC errors
    if "error" in data:
        error = data["error"]
        raise MCPRPCError(
            error.get("code", -1),
            error.get("message", "unknown error"),
            request_id
        )
    
    # Validate response structure
    if "result" not in data:
        raise MCPRPCError(-32000, "invalid JSON-RPC response: missing result and error", request_id)
    
    return data


def extract_session_id(response: httpx.Response) -> str:
    """Extract session ID from response headers."""
    session_id = response.headers.get("Mcp-Session-Id")
    if session_id and session_id.strip():
        return session_id.strip()
    return None


def is_session_required_error(status_code: int, error_message: str) -> bool:
    """Check if error indicates session is required."""
    return (status_code in (401, 412) or 
            "session required" in error_message.lower())


async def send_notification(client: httpx.AsyncClient, base_url: str, headers: Dict[str, str]):
    """Send initialized notification (best effort)."""
    try:
        notification = build_notification_payload()
        await client.post(base_url, json=notification, headers=headers)
    except Exception:
        # Ignore notification errors
        pass


async def close_session(client: httpx.AsyncClient, base_url: str, headers: Dict[str, str]):
    """Close MCP session with DELETE request."""
    try:
        await client.delete(base_url, headers=headers)
    except Exception:
        # Ignore all errors during close
        pass


async def close_http_client(client: httpx.AsyncClient):
    """Close HTTP client safely."""
    try:
        await client.aclose()
    except Exception:
        # Ignore double-close errors
        pass


def validate_base_url(base_url: str) -> None:
    """Validate base URL format."""
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ValueError("base_url must be http(s)")


def get_timeout_ms(timeout: int = None) -> int:
    """Get timeout in milliseconds from env or default."""
    import os
    return timeout or int(os.getenv('ORCH_TIMEOUT_MS_DEFAULT', '8000'))


def reset_client_state(client):
    """Reset client state for session retry."""
    client.state = "new"
    client.session_id = None
