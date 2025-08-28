"""Test orchestrator Sales agent functionality with MCP and REST protocols."""

import pytest
from unittest.mock import patch, AsyncMock
from app.services.orchestrator import orchestrate_brief
from app.models import ExternalAgent


@pytest.fixture
def mock_tenant():
    """Create mock tenant."""
    class MockTenant:
        def __init__(self):
            self.id = 1
            self.name = "Test Tenant"
            self.slug = "test-tenant"
    return MockTenant()


@pytest.fixture
def mock_external_agent():
    """Create mock external agent."""
    return ExternalAgent(
        id=1,
        name="Test Signals Agent",
        base_url="http://test-signals.com",
        agent_type="signals",
        protocol="mcp"
    )


@patch('app.services.orchestrator.get_tenant_by_id')
@patch('app.services._orchestrator_agents.call_sales_agent')
async def test_orchestrate_brief_sales_mcp_success(mock_call_sales, mock_get_tenant, mock_tenant):
    """Test successful orchestration with Sales MCP agent."""
    # Setup mocks
    mock_get_tenant.return_value = mock_tenant
    mock_call_sales.return_value = {
        "agent": {"name": "Test Tenant", "url": "http://localhost:8000/mcp/agents/test-tenant/rpc", "type": "sales", "protocol": "mcp"},
        "ok": True,
        "items": [
            {"product_id": 1, "reason": "Good match", "score": 0.8},
            {"product_id": 2, "reason": "Decent match", "score": 0.6}
        ],
        "error": None
    }
    
    # Call orchestrator
    result = await orchestrate_brief("Find banner ads", [1], [])
    
    # Verify results
    assert "results" in result
    assert "signals" in result
    assert len(result["results"]) == 1
    assert len(result["signals"]) == 0
    
    sales_result = result["results"][0]
    assert sales_result["ok"] is True
    assert sales_result["agent"]["name"] == "Test Tenant"
    assert sales_result["agent"]["type"] == "sales"
    assert sales_result["agent"]["protocol"] == "mcp"
    assert len(sales_result["items"]) == 2
    assert sales_result["error"] is None


@patch('app.services.orchestrator.get_tenant_by_id')
async def test_orchestrate_brief_unknown_tenant(mock_get_tenant):
    """Test orchestration with unknown tenant ID."""
    # Setup mock to return None (unknown tenant)
    mock_get_tenant.return_value = None
    
    # Call orchestrator
    result = await orchestrate_brief("Find banner ads", [999], [])
    
    # Verify error result
    assert len(result["results"]) == 1
    sales_result = result["results"][0]
    assert sales_result["ok"] is False
    assert sales_result["agent"]["name"] == "tenant-999"
    assert "invalid params: tenant id 999 not found" in sales_result["error"]


@patch('app.services.orchestrator.get_tenant_by_id')
@patch('app.services._orchestrator_agents.call_sales_agent')
async def test_orchestrate_brief_sales_error(mock_call_sales, mock_get_tenant, mock_tenant):
    """Test orchestration with Sales agent error."""
    # Setup mocks
    mock_get_tenant.return_value = mock_tenant
    mock_call_sales.return_value = {
        "agent": {"name": "Test Tenant", "url": "http://localhost:8000/mcp/agents/test-tenant/rpc", "type": "sales", "protocol": "mcp"},
        "ok": False,
        "items": None,
        "error": "timeout after 8000ms"
    }
    
    # Call orchestrator
    result = await orchestrate_brief("Find banner ads", [1], [])
    
    # Verify error result
    sales_result = result["results"][0]
    assert sales_result["ok"] is False
    assert "timeout after 8000ms" in sales_result["error"]


@patch('app.services.orchestrator.get_tenant_by_id')
@patch('app.services._orchestrator_agents.call_sales_agent')
@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrate_brief_mixed_success(mock_call_signals, mock_call_sales, mock_get_tenant, mock_tenant, mock_external_agent):
    """Test orchestration with both Sales and Signals agents."""
    # Setup mocks
    mock_get_tenant.return_value = mock_tenant
    mock_call_sales.return_value = {
        "agent": {"name": "Test Tenant", "url": "http://localhost:8000/mcp/agents/test-tenant/rpc", "type": "sales", "protocol": "mcp"},
        "ok": True,
        "items": [{"product_id": 1, "reason": "Good match", "score": 0.8}],
        "error": None
    }
    mock_call_signals.return_value = {
        "agent": {"name": "Test Signals Agent", "url": "http://test-signals.com", "type": "signals", "protocol": "mcp"},
        "ok": True,
        "items": [{"signal_id": "sig1", "name": "Signal 1", "reason": "Good signal", "score": 0.9}],
        "error": None
    }
    
    # Call orchestrator
    result = await orchestrate_brief("Find banner ads", [1], [mock_external_agent])
    
    # Verify results
    assert len(result["results"]) == 1
    assert len(result["signals"]) == 1
    
    sales_result = result["results"][0]
    signals_result = result["signals"][0]
    
    assert sales_result["ok"] is True
    assert signals_result["ok"] is True
    assert sales_result["agent"]["type"] == "sales"
    assert signals_result["agent"]["type"] == "signals"


def test_orchestrate_brief_empty_brief():
    """Test orchestration with empty brief."""
    with pytest.raises(ValueError, match="brief cannot be empty"):
        # This will fail at the start of the function
        import asyncio
        asyncio.run(orchestrate_brief("", [1], []))


@patch('app.services.orchestrator.get_tenant_by_id')
@patch('app.services._orchestrator_agents.call_sales_agent')
async def test_orchestrate_brief_multiple_tenants(mock_call_sales, mock_get_tenant, mock_tenant):
    """Test orchestration with multiple tenants."""
    # Setup mocks
    mock_get_tenant.return_value = mock_tenant
    mock_call_sales.return_value = {
        "agent": {"name": "Test Tenant", "url": "http://localhost:8000/mcp/agents/test-tenant/rpc", "type": "sales", "protocol": "mcp"},
        "ok": True,
        "items": [{"product_id": 1, "reason": "Good match", "score": 0.8}],
        "error": None
    }
    
    # Call orchestrator with multiple tenant IDs
    result = await orchestrate_brief("Find banner ads", [1, 2, 3], [])
    
    # Verify multiple calls were made
    assert len(result["results"]) == 3
    assert mock_call_sales.call_count == 3

