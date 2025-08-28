"""
Test MCP client basic functionality with MockTransport.
"""

import pytest
import httpx
from unittest.mock import Mock

from app.services.mcp_client import MCPClient
from app.services.mcp_errors import MCPConfigError, MCPHTTPError, MCPRPCError, MCPTimeoutError


@pytest.fixture
def mock_transport():
    """Create a mock transport for testing."""
    return httpx.MockTransport


def test_client_initialization():
    """Test client initialization with valid and invalid URLs."""
    # Valid URL
    client = MCPClient("https://example.com/mcp")
    assert client.base_url == "https://example.com/mcp"
    assert client.state == "new"
    assert client.session_id is None
    assert client.id_counter == 1
    
    # Invalid URL
    with pytest.raises(MCPConfigError, match="base_url must be http\\(s\\)"):
        MCPClient("ftp://example.com")
    
    with pytest.raises(MCPConfigError, match="base_url must be http\\(s\\)"):
        MCPClient("not-a-url")


@pytest.mark.asyncio
async def test_open_session_success():
    """Test successful session opening with and without session ID."""
    
    def mock_handler(request):
        # Mock successful initialize response
        if request.method == "POST" and "initialize" in request.content.decode():
            headers = {"Mcp-Session-Id": "test-session-123"}
            
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}},
                headers=headers
            )
        elif request.method == "POST" and "notifications/initialized" in request.content.decode():
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": None})
        else:
            return httpx.Response(404)
    
    transport = httpx.MockTransport(mock_handler)
    
    # Test with session ID
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        await client.open()
        assert client.state == "open"
        assert client.session_id == "test-session-123"
    
    # Test without session ID
    def mock_handler_no_session(request):
        if request.method == "POST" and "initialize" in request.content.decode():
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
            )
        elif request.method == "POST" and "notifications/initialized" in request.content.decode():
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": None})
        else:
            return httpx.Response(404)
    
    transport = httpx.MockTransport(mock_handler_no_session)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        await client.open()
        assert client.state == "open"
        assert client.session_id is None


@pytest.mark.asyncio
async def test_open_session_errors():
    """Test session opening with various error conditions."""
    
    # HTTP error
    def mock_http_error(request):
        return httpx.Response(500, text="Internal Server Error")
    
    transport = httpx.MockTransport(mock_http_error)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        with pytest.raises(MCPHTTPError) as exc_info:
            await client.open()
        assert exc_info.value.status_code == 500
    
    # RPC error
    def mock_rpc_error(request):
        return httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found"}}
        )
    
    transport = httpx.MockTransport(mock_rpc_error)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        with pytest.raises(MCPRPCError) as exc_info:
            await client.open()
        assert exc_info.value.code == -32601
        assert "Method not found" in exc_info.value.message
    
    # Invalid JSON
    def mock_invalid_json(request):
        return httpx.Response(200, text="not json")
    
    transport = httpx.MockTransport(mock_invalid_json)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        with pytest.raises(MCPRPCError) as exc_info:
            await client.open()
        assert exc_info.value.code == -32000


@pytest.mark.asyncio
async def test_call_success():
    """Test successful RPC calls."""
    
    def mock_handler(request):
        if "initialize" in request.content.decode():
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
            )
        elif "notifications/initialized" in request.content.decode():
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": None})
        else:
            # Mock successful method call
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 2, "result": {"data": "test result"}}
            )
    
    transport = httpx.MockTransport(mock_handler)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        await client.open()
        result = await client.call("test_method", {"param": "value"})
        assert result == {"data": "test result"}


@pytest.mark.asyncio
async def test_call_rpc_errors():
    """Test RPC calls that return errors."""
    
    def mock_handler(request):
        if "initialize" in request.content.decode():
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
            )
        elif "notifications/initialized" in request.content.decode():
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": None})
        else:
            # Mock RPC error
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 2, "error": {"code": -32602, "message": "Invalid params"}}
            )
    
    transport = httpx.MockTransport(mock_handler)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        await client.open()
        with pytest.raises(MCPRPCError) as exc_info:
            await client.call("test_method", {"param": "value"})
        assert exc_info.value.code == -32602
        assert "Invalid params" in exc_info.value.message


@pytest.mark.asyncio
async def test_call_http_errors():
    """Test RPC calls that return HTTP errors."""
    
    def mock_handler(request):
        if "initialize" in request.content.decode():
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
            )
        elif "notifications/initialized" in request.content.decode():
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": None})
        else:
            # Mock HTTP error
            return httpx.Response(404, text="Not Found")
    
    transport = httpx.MockTransport(mock_handler)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        await client.open()
        with pytest.raises(MCPHTTPError) as exc_info:
            await client.call("test_method", {"param": "value"})
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_call_timeout():
    """Test RPC calls that timeout."""
    
    def mock_handler(request):
        if "initialize" in request.content.decode():
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
            )
        elif "notifications/initialized" in request.content.decode():
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": None})
        else:
            # Mock timeout for method calls
            raise httpx.TimeoutException("Request timed out")
    
    transport = httpx.MockTransport(mock_handler)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp", timeout=5000)
        client.client = http_client
        
        await client.open()
        with pytest.raises(MCPTimeoutError) as exc_info:
            await client.call("test_method", {"param": "value"})
        assert exc_info.value.timeout_ms == 5000


@pytest.mark.asyncio
async def test_session_retry_logic():
    """Test auto-retry logic for session-required errors."""
    
    call_count = 0
    
    def mock_handler(request):
        nonlocal call_count
        call_count += 1
        
        if "initialize" in request.content.decode():
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}},
                headers={"Mcp-Session-Id": "retry-session-123"}
            )
        elif "notifications/initialized" in request.content.decode():
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": None})
        else:
            # First call fails with session required, second succeeds
            if call_count == 3:  # First method call
                return httpx.Response(
                    401,
                    text="Unauthorized - session required"
                )
            else:  # Second method call after retry
                return httpx.Response(
                    200,
                    json={"jsonrpc": "2.0", "id": 3, "result": {"data": "success after retry"}}
                )
    
    transport = httpx.MockTransport(mock_handler)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        await client.open()
        result = await client.call("test_method", {"param": "value"})
        assert result == {"data": "success after retry"}


@pytest.mark.asyncio
async def test_close_session():
    """Test session closing scenarios."""
    
    def mock_handler(request):
        if "initialize" in request.content.decode():
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}},
                headers={"Mcp-Session-Id": "test-session-123"}
            )
        elif "notifications/initialized" in request.content.decode():
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": None})
        elif request.method == "DELETE":
            # Mock successful close
            return httpx.Response(200)
        else:
            return httpx.Response(404)
    
    transport = httpx.MockTransport(mock_handler)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        await client.open()
        assert client.state == "open"
        assert client.session_id == "test-session-123"
        
        await client.close()
        assert client.state == "closed"
        assert client.session_id is None


@pytest.mark.asyncio
async def test_client_state_management():
    """Test client state transitions and validation."""
    client = MCPClient("https://example.com/mcp")
    
    # Cannot call before open
    with pytest.raises(MCPConfigError, match="client is not open"):
        await client.call("test", {})
    
    # Cannot open twice
    def mock_handler(request):
        if "initialize" in request.content.decode():
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
            )
        elif "notifications/initialized" in request.content.decode():
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": None})
        else:
            return httpx.Response(404)
    
    transport = httpx.MockTransport(mock_handler)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client.client = http_client
        await client.open()
        
        with pytest.raises(MCPConfigError, match="client is not in 'new' state"):
            await client.open()
    
            # Cannot call after close
        closed_client = MCPClient("https://example.com/mcp")
        closed_client.state = "closed"
        with pytest.raises(MCPConfigError, match="client is not open"):
            await closed_client.call("test", {})
    
        # Params validation
        with pytest.raises(MCPConfigError, match="params must be a dict"):
            await client.call("test", "not a dict")


@pytest.mark.asyncio
async def test_invalid_json_rpc():
    """Test handling of invalid JSON-RPC responses."""
    
    def mock_handler(request):
        if "initialize" in request.content.decode():
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
            )
        elif "notifications/initialized" in request.content.decode():
            return httpx.Response(200, json={"jsonrpc": "2.0", "result": None})
        else:
            # Mock invalid JSON-RPC response (no result or error)
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": 2}
            )
    
    transport = httpx.MockTransport(mock_handler)
    
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = MCPClient("https://example.com/mcp")
        client.client = http_client
        
        await client.open()
        with pytest.raises(MCPRPCError) as exc_info:
            await client.call("test_method", {"param": "value"})
        assert exc_info.value.code == -32000
        assert "missing result and error" in exc_info.value.message
