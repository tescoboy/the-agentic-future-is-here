"""Test orchestrator circuit breaker functionality."""

import pytest
import time
from unittest.mock import patch, AsyncMock
from app.services.orchestrator import orchestrate_brief
from app.services._orchestrator_breaker import (
    check_circuit_breaker, record_circuit_breaker_failure, reset_circuit_breaker
)
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


def test_circuit_breaker_initial_state():
    """Test circuit breaker initial state."""
    # Should not be tripped initially
    assert not check_circuit_breaker("http://test.com")


def test_circuit_breaker_failure_recording():
    """Test circuit breaker failure recording."""
    base_url = "http://test.com"
    config = {"cb_fails": 2, "cb_ttl_s": 60}
    
    # Record first failure
    record_circuit_breaker_failure(base_url, config)
    assert not check_circuit_breaker(base_url)  # Not tripped yet
    
    # Record second failure (should trip)
    record_circuit_breaker_failure(base_url, config)
    assert check_circuit_breaker(base_url)  # Should be tripped


def test_circuit_breaker_reset():
    """Test circuit breaker reset on success."""
    base_url = "http://test.com"
    config = {"cb_fails": 1, "cb_ttl_s": 60}
    
    # Trip the breaker
    record_circuit_breaker_failure(base_url, config)
    assert check_circuit_breaker(base_url)
    
    # Reset on success
    reset_circuit_breaker(base_url)
    assert not check_circuit_breaker(base_url)


def test_circuit_breaker_cooldown():
    """Test circuit breaker cooldown period."""
    base_url = "http://test.com"
    config = {"cb_fails": 1, "cb_ttl_s": 1}  # 1 second cooldown
    
    # Trip the breaker
    record_circuit_breaker_failure(base_url, config)
    assert check_circuit_breaker(base_url)
    
    # Wait for cooldown to expire
    time.sleep(1.1)
    assert not check_circuit_breaker(base_url)


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrator_circuit_breaker_trip(mock_call_signals, mock_signals_agent):
    """Test that orchestrator respects circuit breaker."""
    # Setup mock to simulate repeated failures
    mock_call_signals.side_effect = Exception("connection failed")
    
    # Call orchestrator multiple times
    for i in range(3):
        result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent])
        signals_result = result["signals"][0]
        
        if i < 2:
            # First two calls should fail but not trip breaker
            assert signals_result["ok"] is False
            assert "connection failed" in signals_result["error"]
        else:
            # Third call should trip circuit breaker
            assert signals_result["ok"] is False
            assert "circuit breaker open" in signals_result["error"]


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrator_circuit_breaker_recovery(mock_call_signals, mock_signals_agent):
    """Test circuit breaker recovery after cooldown."""
    # Setup mock to fail then succeed
    call_count = 0
    def mock_call(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception("connection failed")
        else:
            return {
                "agent": {"name": "Test Signals Agent", "url": "http://test-signals.com", "type": "signals", "protocol": "mcp"},
                "ok": True,
                "items": [{"signal_id": "sig1", "name": "Signal 1", "reason": "Good signal", "score": 0.9}],
                "error": None
            }
    
    mock_call_signals.side_effect = mock_call
    
    # First two calls should fail and trip breaker
    for i in range(2):
        result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent])
        signals_result = result["signals"][0]
        assert signals_result["ok"] is False
    
    # Third call should be blocked by circuit breaker
    result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent])
    signals_result = result["signals"][0]
    assert signals_result["ok"] is False
    assert "circuit breaker open" in signals_result["error"]
    
    # Reset circuit breaker manually for testing
    reset_circuit_breaker("http://test-signals.com")
    
    # Next call should succeed
    result = await orchestrate_brief("Find banner ads", [], [mock_signals_agent])
    signals_result = result["signals"][0]
    assert signals_result["ok"] is True
    assert len(signals_result["items"]) == 1


@patch('app.services._orchestrator_agents.call_signals_agent')
async def test_orchestrator_circuit_breaker_per_agent(mock_call_signals):
    """Test that circuit breaker is per-agent."""
    # Create two different agents
    agent1 = ExternalAgent(
        id=1, name="Agent 1", base_url="http://agent1.com", 
        agent_type="signals", protocol="mcp"
    )
    agent2 = ExternalAgent(
        id=2, name="Agent 2", base_url="http://agent2.com", 
        agent_type="signals", protocol="mcp"
    )
    
    # Setup mock to fail for agent1, succeed for agent2
    def mock_call(*args, **kwargs):
        agent = args[0]  # First argument is the agent
        if agent.base_url == "http://agent1.com":
            raise Exception("agent1 failed")
        else:
            return {
                "agent": {"name": agent.name, "url": agent.base_url, "type": "signals", "protocol": "mcp"},
                "ok": True,
                "items": [{"signal_id": "sig1", "name": "Signal 1", "reason": "Good signal", "score": 0.9}],
                "error": None
            }
    
    mock_call_signals.side_effect = mock_call
    
    # Call orchestrator with both agents
    result = await orchestrate_brief("Find banner ads", [], [agent1, agent2])
    
    # Agent1 should fail, Agent2 should succeed
    assert len(result["signals"]) == 2
    assert result["signals"][0]["ok"] is False  # agent1 failed
    assert result["signals"][1]["ok"] is True   # agent2 succeeded
    
    # Call again - agent1 should be blocked by circuit breaker, agent2 should still succeed
    result = await orchestrate_brief("Find banner ads", [], [agent1, agent2])
    assert result["signals"][0]["ok"] is False
    assert "circuit breaker open" in result["signals"][0]["error"]
    assert result["signals"][1]["ok"] is True

