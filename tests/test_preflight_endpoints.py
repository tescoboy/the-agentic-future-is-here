"""Unit tests for preflight endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db import get_session
from app.models import Tenant, ExternalAgent


@pytest.fixture
def client():
    """Test client with overridden database session."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def sample_tenant():
    """Sample tenant for testing."""
    return Tenant(
        id=1,
        slug="test-tenant",
        name="Test Tenant",
        enabled=True
    )


@pytest.fixture
def sample_external_agent():
    """Sample external agent for testing."""
    return ExternalAgent(
        id=1,
        name="Test Signals Agent",
        base_url="https://signals.example.com/mcp",
        agent_type="signals",
        protocol="mcp",
        enabled=True
    )


def test_preflight_json_endpoint(client, mock_session):
    """Test preflight JSON endpoint returns correct structure."""
    with patch('app.db.get_session', return_value=mock_session):
        # Mock the preflight data generation
        mock_data = {
            "ok": True,
            "service": "adcp-demo",
            "version": "0.1.0",
            "env": {
                "DB_URL": "",
                "SERVICE_BASE_URL": "",
                "ORCH_TIMEOUT_MS_DEFAULT": 25000,
                "ORCH_CONCURRENCY": 8,
                "CB_FAILS": 2,
                "CB_TTL_S": 60,
                "MCP_SESSION_TTL_S": 60,
                "DEBUG": 0
            },
            "paths": {
                "data_dir_exists": True,
                "db_file_exists": True,
                "db_writeable": True,
                "mcp_routes_mounted": True
            },
            "reference": {
                "salesagent_commit": "abc1234",
                "signalsagent_commit": "def5678",
                "present": True
            },
            "db_schema": {
                "external_agents_has_agent_type": True,
                "external_agents_has_protocol": True
            },
            "agents": {
                "enabled_sales": {"rest": 0, "mcp": 1},
                "enabled_signals": {"rest": 0, "mcp": 1}
            },
            "tenants": {
                "count": 1,
                "with_custom_prompts": 0,
                "using_default_prompts": 1
            }
        }
        
        with patch('app.routes.preflight.endpoints.get_preflight_data', return_value=mock_data):
            response = client.get("/preflight/status")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required top-level fields
            assert "ok" in data
            assert "service" in data
            assert "version" in data
            assert "env" in data
            assert "paths" in data
            assert "reference" in data
            assert "db_schema" in data
            assert "agents" in data
            assert "tenants" in data
            
            # Check environment variables
            env = data["env"]
            assert "DB_URL" in env
            assert "SERVICE_BASE_URL" in env
            assert "ORCH_TIMEOUT_MS_DEFAULT" in env
            assert "ORCH_CONCURRENCY" in env
            assert "CB_FAILS" in env
            assert "CB_TTL_S" in env
            assert "MCP_SESSION_TTL_S" in env
            assert "DEBUG" in env
            
            # Check path checks
            paths = data["paths"]
            assert "data_dir_exists" in paths
            assert "db_file_exists" in paths
            assert "db_writeable" in paths
            assert "mcp_routes_mounted" in paths
            
            # Check reference data
            reference = data["reference"]
            assert "salesagent_commit" in reference
            assert "signalsagent_commit" in reference
            assert "present" in reference
            
            # Check database schema
            db_schema = data["db_schema"]
            assert "external_agents_has_agent_type" in db_schema
            assert "external_agents_has_protocol" in db_schema
            
            # Check agents
            agents = data["agents"]
            assert "enabled_sales" in agents
            assert "enabled_signals" in agents
            
            # Check tenants
            tenants = data["tenants"]
            assert "count" in tenants
            assert "with_custom_prompts" in tenants
            assert "using_default_prompts" in tenants


def test_preflight_ui_endpoint(client, mock_session, sample_tenant, sample_external_agent):
    """Test preflight UI endpoint returns HTML dashboard."""
    with patch('app.db.get_session', return_value=mock_session):
        # Mock the preflight data generation
        mock_data = {
            "ok": True,
            "service": "adcp-demo",
            "version": "0.1.0",
            "env": {
                "DB_URL": "",
                "SERVICE_BASE_URL": "",
                "ORCH_TIMEOUT_MS_DEFAULT": 25000,
                "ORCH_CONCURRENCY": 8,
                "CB_FAILS": 2,
                "CB_TTL_S": 60,
                "MCP_SESSION_TTL_S": 60,
                "DEBUG": 0
            },
            "paths": {
                "data_dir_exists": True,
                "db_file_exists": True,
                "db_writeable": True,
                "mcp_routes_mounted": True
            },
            "reference": {
                "salesagent_commit": "abc1234",
                "signalsagent_commit": "def5678",
                "present": True
            },
            "db_schema": {
                "external_agents_has_agent_type": True,
                "external_agents_has_protocol": True
            },
            "agents": {
                "enabled_sales": {"rest": 0, "mcp": 1},
                "enabled_signals": {"rest": 0, "mcp": 1}
            },
            "tenants": {
                "count": 1,
                "with_custom_prompts": 0,
                "using_default_prompts": 1
            }
        }
        
        with patch('app.routes.preflight.endpoints.get_preflight_data', return_value=mock_data):
            response = client.get("/preflight/ui")
            
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            
            # Check for key HTML elements
            html_content = response.text
            assert "Preflight Dashboard" in html_content
            assert "adcp-demo" in html_content
            assert "Environment" in html_content
            assert "Paths" in html_content
            assert "Reference" in html_content
            assert "Database Schema" in html_content
            assert "Agents" in html_content
            assert "Tenants" in html_content
            
            # Check for Bootstrap classes
            assert "container" in html_content
            assert "card" in html_content
            assert "table" in html_content
            
            # Check for status indicators
            assert "badge" in html_content
