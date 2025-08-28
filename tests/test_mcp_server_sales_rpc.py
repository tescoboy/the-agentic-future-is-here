"""Test MCP server Sales RPC functionality."""

import pytest
import time
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.db import get_session
from app.models import Tenant, Product
from app.repos.tenants import create_tenant
from app.repos.products import create_product


@pytest.fixture
def test_db():
    """Create test database session."""
    from app.db import get_engine
    engine = get_engine()
    with Session(engine) as session:
        yield session


@pytest.fixture
def test_tenant(test_db):
    """Create test tenant."""
    import uuid
    unique_slug = f"test-tenant-{uuid.uuid4().hex[:8]}"
    tenant = create_tenant(test_db, "Test Tenant", unique_slug)
    return tenant


@pytest.fixture
def test_products(test_db, test_tenant):
    """Create test products."""
    products = []
    for i in range(3):
        product = create_product(
            test_db, test_tenant.id, f"Product {i+1}", f"Description {i+1}",
            10.0 + i, "banner", "{}", "{}"
        )
        products.append(product)
    return products


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_rank_products_success(client, test_tenant, test_products):
    """Test successful rank_products call."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "rank_products",
        "params": {"brief": "Find banner ads"}
    }
    
    response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert "result" in data
    
    result = data["result"]
    assert "items" in result
    assert len(result["items"]) == 3
    
    # Check session header was created
    assert "Mcp-Session-Id" in response.headers


def test_rank_products_empty_brief(client, test_tenant):
    """Test rank_products with empty brief."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "rank_products",
        "params": {"brief": ""}
    }
    
    response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"]["code"] == -32602
    assert "brief must be a non-empty string" in data["error"]["message"]


def test_rank_products_invalid_tenant(client):
    """Test rank_products with unknown tenant."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "rank_products",
        "params": {"brief": "test"}
    }
    
    response = client.post("/mcp/agents/unknown-tenant/rpc", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"]["code"] == -32602
    assert "tenant 'unknown-tenant' not found" in data["error"]["message"]


def test_invalid_json_rpc_envelope(client, test_tenant):
    """Test invalid JSON-RPC envelope."""
    # Missing jsonrpc
    payload = {
        "id": 1,
        "method": "rank_products",
        "params": {"brief": "test"}
    }
    
    response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"]["code"] == -32600
    assert "jsonrpc must be '2.0'" in data["error"]["message"]


def test_unknown_method(client, test_tenant):
    """Test unknown method."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "unknown_method",
        "params": {}
    }
    
    response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"]["code"] == -32601
    assert "method not found" in data["error"]["message"]


def test_session_management(client, test_tenant, test_products):
    """Test session creation and validation."""
    # First call - should create session
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "rank_products",
        "params": {"brief": "test"}
    }
    
    response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    assert response.status_code == 200
    assert "Mcp-Session-Id" in response.headers
    
    session_id = response.headers["Mcp-Session-Id"]
    
    # Second call - should require session header
    response2 = client.post(
        f"/mcp/agents/{test_tenant.slug}/rpc",
        json=payload,
        headers={"Mcp-Session-Id": session_id}
    )
    assert response2.status_code == 200
    assert "result" in response2.json()


def test_session_required_on_followup(client, test_tenant, test_products):
    """Test that session is required on follow-up calls."""
    # First call - creates session
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "rank_products",
        "params": {"brief": "test"}
    }
    
    response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    assert response.status_code == 200
    
    # Second call without session header - should fail
    response2 = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    assert response2.status_code == 200
    
    data = response2.json()
    assert data["error"]["code"] == -32000
    assert "session required" in data["error"]["message"]


@patch('time.monotonic')
def test_session_expiry(mock_monotonic, client, test_tenant, test_products):
    """Test session expiry."""
    # Set up time mocking
    mock_monotonic.return_value = 1000.0
    
    # First call - creates session
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "rank_products",
        "params": {"brief": "test"}
    }
    
    response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    session_id = response.headers["Mcp-Session-Id"]
    
    # Simulate time passing (session expires)
    mock_monotonic.return_value = 1100.0  # 100 seconds later
    
    # Try to use expired session
    response2 = client.post(
        f"/mcp/agents/{test_tenant.slug}/rpc",
        json=payload,
        headers={"Mcp-Session-Id": session_id}
    )
    
    data = response2.json()
    assert data["error"]["code"] == -32000
    assert "session invalid or expired" in data["error"]["message"]


def test_delete_session(client, test_tenant, test_products):
    """Test DELETE session endpoint."""
    # Create session
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "rank_products",
        "params": {"brief": "test"}
    }
    
    response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    session_id = response.headers["Mcp-Session-Id"]
    
    # Delete session
    response2 = client.delete(
        f"/mcp/agents/{test_tenant.slug}/rpc",
        headers={"Mcp-Session-Id": session_id}
    )
    assert response2.status_code == 200
    assert response2.json() == {"ok": True}


def test_rest_shim_mirrors_mcp(client, test_tenant, test_products):
    """Test REST shim returns same result as MCP."""
    # MCP call
    mcp_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "rank_products",
        "params": {"brief": "Find banner ads"}
    }
    
    mcp_response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=mcp_payload)
    mcp_result = mcp_response.json()["result"]
    
    # REST shim call
    rest_payload = {"brief": "Find banner ads"}
    rest_response = client.post(f"/mcp/agents/{test_tenant.slug}/rank", json=rest_payload)
    rest_result = rest_response.json()
    
    # Results should be identical
    assert rest_result == mcp_result


def test_get_info(client, test_tenant):
    """Test mcp.get_info method."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "mcp.get_info",
        "params": {}
    }
    
    response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    
    result = data["result"]
    assert result["service"] == "adcp-sales"
    assert result["version"] == "0.1.0"
    assert "rank_products" in result["capabilities"]


def test_get_info_no_session_required(client, test_tenant):
    """Test that mcp.get_info doesn't require session."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "mcp.get_info",
        "params": {}
    }
    
    response = client.post(f"/mcp/agents/{test_tenant.slug}/rpc", json=payload)
    assert response.status_code == 200
    assert "Mcp-Session-Id" not in response.headers


def test_server_info(client):
    """Test GET /mcp/ endpoint."""
    response = client.get("/mcp/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "adcp-sales"
    assert data["version"] == "0.1.0"
    assert "description" in data
