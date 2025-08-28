"""Test orchestrator Signals agent functionality with MCP protocol."""

import pytest
from unittest.mock import patch
from app.services.orchestrator import orchestrate_brief
from app.models import ExternalAgent


@pytest.fixture
def mock_signals_agent_mcp():
    """Create mock MCP signals agent."""
    return ExternalAgent(
        id=1,
        name="Test Signals MCP",
        base_url="http://test-signals-mcp.com",
        agent_type="signals",
        protocol="mcp"
    )


@pytest.fixture
def mock_signals_agent_rest():
    """Create mock REST signals agent (invalid)."""
    return ExternalAgent(
        id=2,
        name="Test Signals REST",
        base_url="http://test-signals-rest.com",
        agent_type="signals",
        protocol="rest"
    )


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrate_brief_signals_mcp_success(mock_call_signals, mock_signals_agent_mcp):
    """Test successful orchestration with Signals MCP agent."""
    # Setup mock
    mock_call_signals.return_value = {
        "agent": {"name": "Test Signals MCP", "url": "http://test-signals-mcp.com", "type": "signals", "protocol": "mcp"},
        "ok": True,
        "items": [
            {"signal_id": "sig1", "name": "Signal 1", "reason": "Good signal", "score": 0.9},
            {"signal_id": "sig2", "name": "Signal 2", "reason": "Decent signal", "score": 0.7}
        ],
        "error": None
    }
    
    # Call orchestrator
    result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent_mcp])
    
    # Verify results
    assert len(result["results"]) == 0
    assert len(result["signals"]) == 1
    
    signals_result = result["signals"][0]
    assert signals_result["ok"] is True
    assert signals_result["agent"]["name"] == "Test Signals MCP"
    assert signals_result["agent"]["type"] == "signals"
    assert signals_result["agent"]["protocol"] == "mcp"
    assert len(signals_result["items"]) == 2
    assert signals_result["error"] is None


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrate_brief_signals_mcp_error(mock_call_signals, mock_signals_agent_mcp):
    """Test orchestration with Signals MCP agent error."""
    # Setup mock
    mock_call_signals.return_value = {
        "agent": {"name": "Test Signals MCP", "url": "http://test-signals-mcp.com", "type": "signals", "protocol": "mcp"},
        "ok": False,
        "items": None,
        "error": "timeout after 8000ms"
    }
    
    # Call orchestrator
    result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent_mcp])
    
    # Verify error result
    signals_result = result["signals"][0]
    assert signals_result["ok"] is False
    assert "timeout after 8000ms" in signals_result["error"]


async def test_orchestrate_brief_signals_rest_rejected(mock_signals_agent_rest):
    """Test that REST signals agents are rejected."""
    # Call orchestrator
    result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent_rest])
    
    # Verify rejection
    assert len(result["signals"]) == 1
    signals_result = result["signals"][0]
    assert signals_result["ok"] is False
    assert signals_result["agent"]["protocol"] == "rest"
    assert "signals requires protocol=mcp" in signals_result["error"]


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrate_brief_multiple_signals(mock_call_signals, mock_signals_agent_mcp):
    """Test orchestration with multiple signals agents."""
    # Create second signals agent
    mock_signals_agent_mcp2 = ExternalAgent(
        id=3,
        name="Test Signals MCP 2",
        base_url="http://test-signals-mcp2.com",
        agent_type="signals",
        protocol="mcp"
    )
    
    # Setup mocks
    mock_call_signals.side_effect = [
        {
            "agent": {"name": "Test Signals MCP", "url": "http://test-signals-mcp.com", "type": "signals", "protocol": "mcp"},
            "ok": True,
            "items": [{"signal_id": "sig1", "name": "Signal 1", "reason": "Good signal", "score": 0.9}],
            "error": None
        },
        {
            "agent": {"name": "Test Signals MCP 2", "url": "http://test-signals-mcp2.com", "type": "signals", "protocol": "mcp"},
            "ok": False,
            "items": None,
            "error": "connection failed"
        }
    ]
    
    # Call orchestrator
    result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent_mcp, mock_signals_agent_mcp2])
    
    # Verify results
    assert len(result["signals"]) == 2
    assert mock_call_signals.call_count == 2
    
    # First agent succeeded
    assert result["signals"][0]["ok"] is True
    assert len(result["signals"][0]["items"]) == 1
    
    # Second agent failed
    assert result["signals"][1]["ok"] is False
    assert "connection failed" in result["signals"][1]["error"]


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrate_brief_signals_mixed_protocols(mock_call_signals, mock_signals_agent_mcp, mock_signals_agent_rest):
    """Test orchestration with mixed protocol signals agents."""
    # Setup mock for MCP agent
    mock_call_signals.return_value = {
        "agent": {"name": "Test Signals MCP", "url": "http://test-signals-mcp.com", "type": "signals", "protocol": "mcp"},
        "ok": True,
        "items": [{"signal_id": "sig1", "name": "Signal 1", "reason": "Good signal", "score": 0.9}],
        "error": None
    }
    
    # Call orchestrator with both MCP and REST agents
    result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent_mcp, mock_signals_agent_rest])
    
    # Verify results
    assert len(result["signals"]) == 2
    
    # MCP agent should succeed
    assert result["signals"][0]["ok"] is True
    assert result["signals"][0]["agent"]["protocol"] == "mcp"
    
    # REST agent should be rejected
    assert result["signals"][1]["ok"] is False
    assert result["signals"][1]["agent"]["protocol"] == "rest"
    assert "signals requires protocol=mcp" in result["signals"][1]["error"]

