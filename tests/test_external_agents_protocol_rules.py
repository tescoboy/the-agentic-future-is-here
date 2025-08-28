"""
Test external agents protocol validation rules.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_session
from app.repos.external_agents import create_external_agent

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


def test_create_agent_with_valid_data(temp_db):
    """Test creating agent with valid data."""
    response = client.post("/external-agents/", data={
        "name": "Test Agent",
        "base_url": "https://example.com/api",
        "agent_type": "sales",
        "protocol": "rest",
        "enabled": "true"
    }, allow_redirects=False)
    assert response.status_code == 302  # Redirect after success


def test_create_agent_invalid_agent_type(temp_db):
    """Test creating agent with invalid agent type."""
    response = client.post("/external-agents/", data={
        "name": "Test Agent",
        "base_url": "https://example.com/api",
        "agent_type": "invalid",
        "protocol": "rest",
        "enabled": "true"
    }, allow_redirects=False)
    assert response.status_code == 200  # Form re-rendered with error
    assert "Agent type must be &#39;sales&#39; or &#39;signals&#39;" in response.text


def test_create_agent_invalid_protocol(temp_db):
    """Test creating agent with invalid protocol."""
    response = client.post("/external-agents/", data={
        "name": "Test Agent",
        "base_url": "https://example.com/api",
        "agent_type": "sales",
        "protocol": "invalid",
        "enabled": "true"
    }, allow_redirects=False)
    assert response.status_code == 200  # Form re-rendered with error
    assert "Protocol must be &#39;rest&#39; or &#39;mcp&#39;" in response.text


def test_create_agent_invalid_base_url(temp_db):
    """Test creating agent with invalid base URL."""
    response = client.post("/external-agents/", data={
        "name": "Test Agent",
        "base_url": "ftp://example.com/api",
        "agent_type": "sales",
        "protocol": "rest",
        "enabled": "true"
    }, allow_redirects=False)
    assert response.status_code == 200  # Form re-rendered with error
    assert "base_url must start with http:// or https://" in response.text


def test_create_agent_long_base_url_truncated(temp_db):
    """Test that long base URLs are truncated in error messages."""
    long_url = "ftp://" + "x" * 300
    response = client.post("/external-agents/", data={
        "name": "Test Agent",
        "base_url": long_url,
        "agent_type": "sales",
        "protocol": "rest",
        "enabled": "true"
    }, allow_redirects=False)
    assert response.status_code == 200
    assert "base_url must start with http:// or https://. Got: ftp://" in response.text
    # Should be truncated to ~200 chars
    import re
    error_match = re.search(r'Got:.*?ftp://', response.text)
    assert error_match is not None
    assert len(error_match.group(0)) <= 200


def test_edit_agent_validation(temp_db):
    """Test edit form validation."""
    # First create a valid agent
    with patch('app.routes.external_agents.get_session') as mock_session:
        mock_session.return_value = get_session().__next__()
        create_external_agent(mock_session.return_value, "Test Agent", 
                            "https://example.com/api", True, "sales", "rest")
    
    # Try to edit with invalid data
    response = client.post("/external-agents/1/edit", data={
        "name": "Updated Agent",
        "base_url": "invalid-url",
        "agent_type": "sales",
        "protocol": "rest",
        "enabled": "true"
    }, allow_redirects=False)
    assert response.status_code == 200
    assert "base_url must start with http:// or https://" in response.text
