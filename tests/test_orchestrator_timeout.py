"""Test orchestrator timeout functionality."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from app.services.orchestrator import orchestrate_brief
from app.models import ExternalAgent


@pytest.fixture
def mock_signals_agent():
    """Create mock signals agent."""
    return ExternalAgent(
        id=1,
        name="Test Signals Agent",
        base_url="http://test-signals.com",
        agent_type="signals",
        protocol="mcp"
    )


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrator_timeout_error(mock_call_signals, mock_signals_agent):
    """Test orchestrator timeout error handling."""
    # Setup mock to simulate timeout
    mock_call_signals.side_effect = Exception("timeout after 8000ms")
    
    # Call orchestrator
    result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent])
    
    # Verify timeout error
    signals_result = result["signals"][0]
    assert signals_result["ok"] is False
    assert "timeout after 8000ms" in signals_result["error"]


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrator_slow_agent_timeout(mock_call_signals, mock_signals_agent):
    """Test orchestrator with slow agent that times out."""
    # Setup mock to simulate slow response
    async def slow_response(*args, **kwargs):
        await asyncio.sleep(0.1)  # Simulate slow response
        raise Exception("timeout after 8000ms")
    
    mock_call_signals.side_effect = slow_response
    
    # Call orchestrator
    result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent])
    
    # Verify timeout error
    signals_result = result["signals"][0]
    assert signals_result["ok"] is False
    assert "timeout after 8000ms" in signals_result["error"]


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrator_timeout_doesnt_affect_others(mock_call_signals):
    """Test that timeout on one agent doesn't affect others."""
    # Create two agents
    agent1 = ExternalAgent(
        id=1, name="Slow Agent", base_url="http://slow-agent.com", 
        agent_type="signals", protocol="mcp"
    )
    agent2 = ExternalAgent(
        id=2, name="Fast Agent", base_url="http://fast-agent.com", 
        agent_type="signals", protocol="mcp"
    )
    
    # Setup mock to timeout for agent1, succeed for agent2
    def mock_call(*args, **kwargs):
        agent = args[0]
        if agent.base_url == "http://slow-agent.com":
            raise Exception("timeout after 8000ms")
        else:
            return {
                "agent": {"name": agent.name, "url": agent.base_url, "type": "signals", "protocol": "mcp"},
                "ok": True,
                "items": [{"signal_id": "sig1", "name": "Signal 1", "reason": "Fast response", "score": 0.9}],
                "error": None
            }
    
    mock_call_signals.side_effect = mock_call
    
    # Call orchestrator with both agents
    result = await orchestrate_brief("Find banner ads", [], [agent1, agent2])
    
    # Verify results
    assert len(result["signals"]) == 2
    
    # Slow agent should timeout
    assert result["signals"][0]["ok"] is False
    assert "timeout after 8000ms" in result["signals"][0]["error"]
    
    # Fast agent should succeed
    assert result["signals"][1]["ok"] is True
    assert len(result["signals"][1]["items"]) == 1


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrator_different_timeout_messages(mock_call_signals, mock_signals_agent):
    """Test orchestrator with different timeout error messages."""
    # Test various timeout-related error messages
    timeout_messages = [
        "timeout after 8000ms",
        "timeout after 5000ms", 
        "connection timeout",
        "request timeout"
    ]
    
    for timeout_msg in timeout_messages:
        mock_call_signals.side_effect = Exception(timeout_msg)
        
        result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent])
        signals_result = result["signals"][0]
        
        assert signals_result["ok"] is False
        assert timeout_msg in signals_result["error"]


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrator_non_timeout_errors(mock_call_signals, mock_signals_agent):
    """Test orchestrator with non-timeout errors."""
    # Test various non-timeout error messages
    error_messages = [
        "connection refused",
        "invalid response",
        "server error",
        "network error"
    ]
    
    for error_msg in error_messages:
        mock_call_signals.side_effect = Exception(error_msg)
        
        result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent])
        signals_result = result["signals"][0]
        
        assert signals_result["ok"] is False
        assert error_msg in signals_result["error"]
        # Should not contain "timeout after" for non-timeout errors
        assert "timeout after" not in signals_result["error"]

