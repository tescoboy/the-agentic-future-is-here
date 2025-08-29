"""Unit tests for tenant prompt admin functionality."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.models import Tenant

client = TestClient(app)


@pytest.fixture
def sample_tenant():
    """Sample tenant for testing."""
    return Tenant(
        id=1,
        slug="test-tenant",
        name="Test Tenant",
        enabled=True,
        custom_prompt="Custom prompt for testing"
    )


def test_prompt_admin_form_shows_default_and_custom(mock_session):
    """Test that prompt admin form shows both default and custom prompts."""
    with patch('app.routes.tenants.prompt.get_tenant_by_id') as mock_get_tenant:
        mock_tenant = MagicMock()
        mock_tenant.id = 1
        mock_tenant.name = "Test Tenant"
        mock_tenant.slug = "test-tenant"
        mock_tenant.custom_prompt = "Custom prompt text"
        mock_get_tenant.return_value = mock_tenant
        
        response = client.get("/tenants/1/prompt")
        
        assert response.status_code == 200
        assert "Default Sales Prompt" in response.text
        assert "Custom Prompt" in response.text
        assert "Custom prompt text" in response.text


def test_prompt_admin_form_without_custom_prompt(mock_session):
    """Test that prompt admin form works without custom prompt."""
    with patch('app.routes.tenants.prompt.get_tenant_by_id') as mock_get_tenant:
        mock_tenant = MagicMock()
        mock_tenant.id = 1
        mock_tenant.name = "Test Tenant"
        mock_tenant.slug = "test-tenant"
        mock_tenant.custom_prompt = None
        mock_get_tenant.return_value = mock_tenant
        
        response = client.get("/tenants/1/prompt")
        
        assert response.status_code == 200
        assert "Default Sales Prompt" in response.text
        assert "Custom Prompt" in response.text
        assert "Custom prompt text" not in response.text


def test_prompt_admin_form_tenant_not_found(mock_session):
    """Test that prompt admin form returns 404 for non-existent tenant."""
    with patch('app.routes.tenants.prompt.get_tenant_by_id') as mock_get_tenant:
        mock_get_tenant.return_value = None
        
        response = client.get("/tenants/999/prompt")
        
        assert response.status_code == 404


def test_update_prompt_too_long_validation_error(mock_session):
    """Test that updating prompt with too long text shows validation error."""
    with patch('app.routes.tenants.prompt.get_tenant_by_id') as mock_get_tenant:
        mock_tenant = MagicMock()
        mock_tenant.id = 1
        mock_tenant.name = "Test Tenant"
        mock_tenant.slug = "test-tenant"
        mock_tenant.custom_prompt = "Existing prompt"
        mock_get_tenant.return_value = mock_tenant
        
        # Create a prompt that's too long (over 8000 characters)
        long_prompt = "A" * 8001
        
        response = client.post("/tenants/1/prompt", data={
            "custom_prompt": long_prompt
        })
        
        assert response.status_code == 200
        assert "Custom prompt must be 8000 characters or less" in response.text
        assert long_prompt in response.text  # Form should preserve the text


def test_update_prompt_tenant_not_found(mock_session):
    """Test that updating prompt for non-existent tenant returns 404."""
    with patch('app.routes.tenants.prompt.get_tenant_by_id') as mock_get_tenant:
        mock_get_tenant.return_value = None
        
        response = client.post("/tenants/999/prompt", data={
            "custom_prompt": "New prompt"
        })
        
        assert response.status_code == 404


def test_tenants_list_shows_custom_prompt_badge(mock_session):
    """Test that tenants list shows badge for tenants with custom prompts."""
    with patch('app.routes.tenants.crud.list_tenants') as mock_list_tenants:
        mock_tenant = MagicMock()
        mock_tenant.id = 1
        mock_tenant.name = "Test Tenant"
        mock_tenant.slug = "test-tenant"
        mock_tenant.custom_prompt = "Custom prompt"
        mock_tenant.created_at = MagicMock()
        mock_tenant.created_at.strftime.return_value = "2024-01-01 12:00"
        
        mock_list_tenants.return_value = ([mock_tenant], 1)
        
        response = client.get("/tenants")
        
        assert response.status_code == 200
        assert "Custom Prompt" in response.text
        assert "badge bg-warning text-dark" in response.text


def test_tenants_list_no_badge_without_custom_prompt():
    """Test that tenants list doesn't show badge for tenants without custom prompts."""
    with patch('app.routes.tenants.crud.list_tenants') as mock_list_tenants:
        mock_tenant = MagicMock()
        mock_tenant.id = 1
        mock_tenant.name = "Test Tenant"
        mock_tenant.slug = "test-tenant"
        mock_tenant.custom_prompt = None
        mock_tenant.created_at = MagicMock()
        mock_tenant.created_at.strftime.return_value = "2024-01-01 12:00"
        
        mock_list_tenants.return_value = ([mock_tenant], 1)
        
        response = client.get("/tenants")
        
        assert response.status_code == 200
        assert "Custom Prompt" not in response.text

@pytest.fixture
def mock_session():
    """Mock database session."""
    with patch('app.db.get_session') as mock:
        session = MagicMock()
        mock.return_value = session
        yield session
