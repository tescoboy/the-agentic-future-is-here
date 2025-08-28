"""
MCP-specific exception classes for JSON-RPC client errors.
"""


class MCPConfigError(Exception):
    """Raised for invalid configuration or client misuse."""
    pass


class MCPHTTPError(Exception):
    """Raised for HTTP non-2xx responses."""
    
    def __init__(self, status_code: int, method: str, url: str, body_preview: str = ""):
        self.status_code = status_code
        self.method = method
        self.url = url
        self.body_preview = body_preview
        super().__init__(f"HTTP {status_code} {method} {url}: {body_preview}")


class MCPRPCError(Exception):
    """Raised for JSON-RPC error responses."""
    
    def __init__(self, code: int, message: str, request_id: int = None):
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(f"RPC error {code}: {message}")


class MCPTimeoutError(Exception):
    """Raised for request timeouts."""
    
    def __init__(self, timeout_ms: int):
        self.timeout_ms = timeout_ms
        super().__init__(f"Request timed out after {timeout_ms}ms")

