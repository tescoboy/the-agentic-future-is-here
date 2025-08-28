"""Tests for publisher endpoint integration feature."""

import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from sqlmodel import Session

from app.main import app
from app.models import Tenant
from app.db import get_session

client = TestClient(app)


@pytest.fixture
def mock_session():
    """Mock database session."""
    with patch('app.routes.publisher.dashboard.get_session') as mock:
        session = MagicMock(spec=Session)
        mock.return_value = session
        yield session


@pytest.fixture
def sample_tenant():
    """Sample tenant for testing."""
    return Tenant(
        id=1,
        name="ACME Corp",
        slug="acme",
        enabled=True
    )


def test_publisher_dashboard_default_endpoint(mock_session, sample_tenant):
    """Test publisher dashboard shows correct endpoint with default env."""
    with patch('app.routes.publisher.dashboard._get_tenant_or_404', return_value=sample_tenant), \
         patch('app.routes.publisher.dashboard.list_products', return_value=([], 0)):
        
        response = client.get("/publisher/acme/")
        assert response.status_code == 200
        
        # Check for Integration card
        assert "Integration" in response.text
        assert "POST http://localhost:8000/mcp/agents/acme/rpc" in response.text


def test_publisher_dashboard_env_override(mock_session, sample_tenant):
    """Test publisher dashboard shows correct endpoint with env override."""
    with patch('app.routes.publisher.dashboard._get_tenant_or_404', return_value=sample_tenant), \
         patch('app.routes.publisher.dashboard.list_products', return_value=([], 0)), \
         patch.dict(os.environ, {'SERVICE_BASE_URL': 'https://demo.example.com/'}):
        
        response = client.get("/publisher/acme/")
        assert response.status_code == 200
        
        # Check for correct endpoint with env override
        assert "POST https://demo.example.com/mcp/agents/acme/rpc" in response.text


def test_publisher_dashboard_url_formatting(mock_session, sample_tenant):
    """Test endpoint URL has no double slashes."""
    with patch('app.routes.publisher.dashboard._get_tenant_or_404', return_value=sample_tenant), \
         patch('app.routes.publisher.dashboard.list_products', return_value=([], 0)), \
         patch.dict(os.environ, {'SERVICE_BASE_URL': 'https://demo.example.com/base/'}):
        
        response = client.get("/publisher/acme/")
        assert response.status_code == 200
        
        # Check for no double slashes
        assert "https://demo.example.com/base/mcp/agents/acme/rpc" in response.text
        assert "//mcp/" not in response.text  # No double slash


def test_publisher_dashboard_slug_escaping(mock_session):
    """Test endpoint URL properly escapes slug characters."""
    tenant_with_special_chars = Tenant(
        id=2,
        name="ACME-Co",
        slug="acme-co",
        enabled=True
    )
    
    with patch('app.routes.publisher.dashboard._get_tenant_or_404', return_value=tenant_with_special_chars), \
         patch('app.routes.publisher.dashboard.list_products', return_value=([], 0)):
        
        response = client.get("/publisher/acme-co/")
        assert response.status_code == 200
        
        # Check for properly escaped slug in URL
        assert "POST http://localhost:8000/mcp/agents/acme-co/rpc" in response.text


def test_publisher_dashboard_integration_card(mock_session, sample_tenant):
    """Test Integration card is present with correct content."""
    with patch('app.routes.publisher.dashboard._get_tenant_or_404', return_value=sample_tenant), \
         patch('app.routes.publisher.dashboard.list_products', return_value=([], 0)):
        
        response = client.get("/publisher/acme/")
        assert response.status_code == 200
        
        # Check for Integration card presence
        assert "Integration" in response.text
        assert "fas fa-plug" in response.text  # Icon
        assert "POST" in response.text  # HTTP method
        assert "endpoint to integrate" in response.text  # Description
        
        # Check for required headers
        assert "Content-Type: application/json" in response.text
        assert "Accept: application/json, text/event-stream" in response.text
        assert "Mcp-Session-Id" in response.text


def test_publisher_dashboard_unknown_slug(mock_session):
    """Test unknown slug returns 404."""
    with patch('app.routes.publisher.dashboard._get_tenant_or_404', 
               side_effect=HTTPException(status_code=404, detail="tenant 'unknown' not found")):
        
        response = client.get("/publisher/unknown/")
        assert response.status_code == 404


def test_get_service_base_url_default():
    """Test get_service_base_url returns default when env not set."""
    from app.utils.env import get_service_base_url
    
    with patch.dict(os.environ, {}, clear=True):
        url = get_service_base_url()
        assert url == "http://localhost:8000"


def test_get_service_base_url_env_override():
    """Test get_service_base_url uses env override."""
    from app.utils.env import get_service_base_url
    
    with patch.dict(os.environ, {'SERVICE_BASE_URL': 'https://demo.example.com/'}):
        url = get_service_base_url()
        assert url == "https://demo.example.com"


def test_get_service_base_url_strips_whitespace():
    """Test get_service_base_url strips whitespace."""
    from app.utils.env import get_service_base_url
    
    with patch.dict(os.environ, {'SERVICE_BASE_URL': '  https://demo.example.com/  '}):
        url = get_service_base_url()
        assert url == "https://demo.example.com"


def test_get_service_base_url_invalid_scheme():
    """Test get_service_base_url raises error for invalid scheme."""
    from app.utils.env import get_service_base_url
    
    with patch.dict(os.environ, {'SERVICE_BASE_URL': 'ftp://demo.example.com'}):
        with pytest.raises(ValueError, match="SERVICE_BASE_URL must start with http:// or https://"):
            get_service_base_url()


def test_get_service_base_url_no_scheme():
    """Test get_service_base_url raises error for no scheme."""
    from app.utils.env import get_service_base_url
    
    with patch.dict(os.environ, {'SERVICE_BASE_URL': 'demo.example.com'}):
        with pytest.raises(ValueError, match="SERVICE_BASE_URL must start with http:// or https://"):
            get_service_base_url()
