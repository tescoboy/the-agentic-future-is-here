"""MCP JSON-RPC client with session lifecycle management."""

import logging
from typing import Dict, Optional
import httpx

from .mcp_errors import MCPConfigError, MCPHTTPError, MCPRPCError, MCPTimeoutError
from ._mcp_helpers import (
    build_init_payload, build_rpc_payload, get_standard_headers,
    handle_http_response, extract_session_id, is_session_required_error,
    send_notification, close_session, close_http_client,
    validate_base_url, get_timeout_ms, reset_client_state
)

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP JSON-RPC client with session lifecycle management."""
    
    def __init__(self, base_url: str, timeout: int = None):
        """Initialize MCP client."""
        try:
            validate_base_url(base_url)
        except ValueError as e:
            raise MCPConfigError(str(e))
        
        self.base_url = base_url
        self.timeout_ms = get_timeout_ms(timeout)
        self.state = "new"
        self.session_id: Optional[str] = None
        self.id_counter = 1
        self.client = httpx.AsyncClient(timeout=self.timeout_ms / 1000.0)
    
    def _next_id(self) -> int:
        """Get next request ID."""
        current = self.id_counter
        self.id_counter += 1
        return current
    
    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for requests."""
        return get_standard_headers(self.session_id)
    
    async def open(self):
        """Open MCP session and capture session ID."""
        if self.state != "new":
            raise MCPConfigError("client is not in 'new' state")
        
        request_id = self._next_id()
        init_payload = build_init_payload(request_id)
        
        try:
            response = await self.client.post(
                self.base_url,
                json=init_payload,
                headers=self._get_headers()
            )
            
            data = handle_http_response(response, request_id, self.base_url)
            
            # Capture session ID
            self.session_id = extract_session_id(response)
            self.state = "open"
            
            # Log session opening
            from urllib.parse import urlparse
            session_info = "short" if self.session_id else "none"
            logger.info(f"opened mcp client base={urlparse(self.base_url).netloc} session={session_info}")
            
            # Send initialized notification (best effort)
            await send_notification(self.client, self.base_url, self._get_headers())
                
        except httpx.TimeoutException:
            raise MCPTimeoutError(self.timeout_ms)
        except (MCPHTTPError, MCPRPCError, MCPTimeoutError):
            raise
        except Exception as e:
            raise MCPConfigError(f"unexpected error during open: {str(e)}")
    
    async def call(self, method: str, params: Dict) -> Dict:
        """Make MCP JSON-RPC call."""
        if self.state != "open":
            raise MCPConfigError("client is not open")
        
        if not isinstance(params, dict):
            raise MCPConfigError("params must be a dict")
        
        request_id = self._next_id()
        payload = build_rpc_payload(request_id, method, params)
        
        try:
            response = await self.client.post(
                self.base_url,
                json=payload,
                headers=self._get_headers()
            )
            
            return await self._handle_call_response(response, request_id, method, params)
            
        except httpx.TimeoutException:
            raise MCPTimeoutError(self.timeout_ms)
        except (MCPHTTPError, MCPRPCError, MCPTimeoutError):
            raise
        except Exception as e:
            raise MCPConfigError(f"unexpected error during call: {str(e)}")
    
    async def _handle_call_response(self, response: httpx.Response, request_id: int, method: str, params: Dict) -> Dict:
        """Handle call response with session retry logic."""
        # Handle HTTP errors with session retry
        if response.status_code < 200 or response.status_code >= 300:
            body_preview = response.text[:200] if response.text else ""
            
            if is_session_required_error(response.status_code, ""):
                return await self._handle_session_retry(method, params)
            
            raise MCPHTTPError(response.status_code, "POST", self.base_url, body_preview)
        
        # Handle JSON-RPC response
        try:
            data = response.json()
        except Exception:
            raise MCPRPCError(-32000, "invalid JSON-RPC response: not valid JSON", request_id)
        
        # Handle RPC errors with session retry
        if "error" in data:
            error = data["error"]
            error_code = error.get("code", -1)
            error_message = error.get("message", "unknown error")
            
            if is_session_required_error(200, error_message):
                return await self._handle_session_retry(method, params)
            
            raise MCPRPCError(error_code, error_message, request_id)
        
        # Validate response structure
        if "result" not in data:
            raise MCPRPCError(-32000, "invalid JSON-RPC response: missing result and error", request_id)
        
        logger.info(f"rpc id={request_id} method={method} outcome=result")
        return data["result"]
    
    async def _handle_session_retry(self, method: str, params: Dict) -> Dict:
        """Handle session-required error with auto-retry."""
        reset_client_state(self)
        
        try:
            await self.open()
        except Exception:
            raise
        
        return await self.call(method, params)
    
    async def close(self):
        """Close MCP session."""
        if self.state == "closed":
            return
        
        if self.session_id:
            await close_session(self.client, self.base_url, self._get_headers())
        
        await close_http_client(self.client)
        
        self.state = "closed"
        self.session_id = None
        
        session_info = "short" if self.session_id else "none"
        logger.info(f"closed mcp client session={session_info}")
