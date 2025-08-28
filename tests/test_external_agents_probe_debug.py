"""
Test external agents probe functionality (DEBUG mode).
"""

import pytest
import httpx
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from app.main import app
from app.utils.probe_utils import is_debug_enabled, probe_mcp_agent, probe_rest_agent
from app.repos.external_agents import create_external_agent
from app.db import get_session

client = TestClient(app)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with patch.dict('os.environ', {'DB_URL': 'sqlite:///./test_temp.db'}):
        from app.db import get_engine, create_all_tables
        engine = get_engine()
        create_all_tables()
        yield
        import os
        if os.path.exists('./test_temp.db'):
            os.remove('./test_temp.db')


def test_is_debug_enabled():
    """Test DEBUG environment variable handling."""
    # Test with different values
    with patch.dict('os.environ', {'DEBUG': '1'}):
        assert is_debug_enabled() is True
    
    with patch.dict('os.environ', {'DEBUG': 'true'}):
        assert is_debug_enabled() is True
    
    with patch.dict('os.environ', {'DEBUG': 'True'}):
        assert is_debug_enabled() is True
    
    with patch.dict('os.environ', {'DEBUG': 'false'}):
        assert is_debug_enabled() is False
    
    with patch.dict('os.environ', {'DEBUG': ''}):
        assert is_debug_enabled() is False


@pytest.mark.asyncio
async def test_probe_mcp_agent_success():
    """Test successful MCP agent probe."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}
    
    with patch('httpx.AsyncClient.post', return_value=mock_response):
        category, message = await probe_mcp_agent("https://example.com/mcp")
        assert category == "success"
        assert "MCP agent responded successfully" in message


@pytest.mark.asyncio
async def test_probe_mcp_agent_method_not_found():
    """Test MCP agent probe with method not found."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "error": {"message": "method not found"}
    }
    
    with patch('httpx.AsyncClient.post', return_value=mock_response):
        category, message = await probe_mcp_agent("https://example.com/mcp")
        assert category == "success"
        assert "mcp.get_info not supported" in message


@pytest.mark.asyncio
async def test_probe_mcp_agent_timeout():
    """Test MCP agent probe timeout."""
    with patch('httpx.AsyncClient.post', side_effect=httpx.TimeoutException("timeout")):
        category, message = await probe_mcp_agent("https://example.com/mcp")
        assert category == "timeout"
        assert "Request timed out" in message


@pytest.mark.asyncio
async def test_probe_rest_agent_success():
    """Test successful REST agent probe."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    
    with patch('httpx.AsyncClient.post', return_value=mock_response):
        category, message = await probe_rest_agent("https://example.com/api")
        assert category == "success"
        assert "REST agent responded successfully" in message


@pytest.mark.asyncio
async def test_probe_rest_agent_invalid_json():
    """Test REST agent probe with invalid JSON response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.side_effect = Exception("Invalid JSON")
    
    with patch('httpx.AsyncClient.post', return_value=mock_response):
        category, message = await probe_rest_agent("https://example.com/api")
        assert category == "invalid_response"
        assert "Non-JSON response" in message


def test_probe_endpoint_debug_disabled(temp_db):
    """Test probe endpoint when DEBUG is disabled."""
    with patch.dict('os.environ', {'DEBUG': 'false'}):
        response = client.post("/external-agents/1/probe")
        assert response.status_code == 403
        assert "Probe not available" in response.text


def test_probe_endpoint_debug_enabled(temp_db):
    """Test probe endpoint when DEBUG is enabled."""
    with patch.dict('os.environ', {'DEBUG': 'true'}):
        # Mock the probe function at the route level
        with patch('app.routes.external_agents.probe_external_agent') as mock_probe:
            mock_probe.return_value = ("success", "Test successful")
            # Mock the get_external_agent_by_id to return a valid agent
            with patch('app.routes.external_agents.get_external_agent_by_id') as mock_get:
                mock_agent = type('MockAgent', (), {
                    'id': 1, 'name': 'Test Agent', 'enabled': True,
                    'agent_type': 'sales', 'protocol': 'rest', 'base_url': 'https://example.com'
                })()
                mock_get.return_value = mock_agent
                # Also mock list_external_agents to return the mock agent
                with patch('app.routes.external_agents.list_external_agents') as mock_list:
                    mock_list.return_value = [mock_agent]
                    response = client.post("/external-agents/1/probe")
                    assert response.status_code == 200
                    assert "Test successful" in response.text


def test_probe_disabled_agent(temp_db):
    """Test probe endpoint with disabled agent."""
    with patch.dict('os.environ', {'DEBUG': 'true'}):
        response = client.post("/external-agents/1/probe")
        assert response.status_code == 404
        assert "Agent not found or disabled" in response.text


def test_probe_nonexistent_agent(temp_db):
    """Test probe endpoint with nonexistent agent."""
    with patch.dict('os.environ', {'DEBUG': 'true'}):
        response = client.post("/external-agents/999/probe")
        assert response.status_code == 404
        assert "Agent not found or disabled" in response.text
