"""
Unit tests for tenant prompt admin functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models import Tenant

client = TestClient(app)


@patch('app.routes.tenants.get_tenant_by_id')
@patch('app.services.sales_contract.get_default_sales_prompt')
def test_prompt_admin_form_shows_default_and_custom(mock_get_default, mock_get_tenant):
    """Test that GET /tenants/{id}/prompt shows default + custom textareas."""
    mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant", custom_prompt="Custom prompt")
    mock_get_tenant.return_value = mock_tenant
    mock_get_default.return_value = "You are an expert media buyer analyzing products"
    
    response = client.get("/tenants/1/prompt")
    
    assert response.status_code == 200
    assert "You are an expert media buyer analyzing products" in response.text
    assert "Custom prompt" in response.text
    assert "Default Sales Prompt" in response.text
    assert "Custom Prompt (Optional)" in response.text


@patch('app.routes.tenants.get_tenant_by_id')
@patch('app.services.sales_contract.get_default_sales_prompt')
def test_prompt_admin_form_without_custom_prompt(mock_get_default, mock_get_tenant):
    """Test prompt admin form when tenant has no custom prompt."""
    mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant", custom_prompt=None)
    mock_get_tenant.return_value = mock_tenant
    mock_get_default.return_value = "You are an expert media buyer analyzing products"
    
    response = client.get("/tenants/1/prompt")
    
    assert response.status_code == 200
    assert "You are an expert media buyer analyzing products" in response.text
    assert "Custom Prompt (Optional)" in response.text


@patch('app.routes.tenants.get_tenant_by_id')
def test_prompt_admin_form_tenant_not_found(mock_get_tenant):
    """Test prompt admin form with non-existent tenant."""
    mock_get_tenant.return_value = None
    
    response = client.get("/tenants/999/prompt")
    
    assert response.status_code == 404


@patch('app.routes.tenants.get_tenant_by_id')
@patch('app.services.sales_contract.get_default_sales_prompt')
def test_update_prompt_too_long_validation_error(mock_get_default, mock_get_tenant):
    """Test POST >8000 chars → actionable validation error."""
    mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant", custom_prompt=None)
    mock_get_tenant.return_value = mock_tenant
    mock_get_default.return_value = "You are an expert media buyer analyzing products"
    
    # Create a prompt longer than 8000 characters
    long_prompt = "x" * 8001
    
    response = client.post("/tenants/1/prompt", data={"custom_prompt": long_prompt})
    
    assert response.status_code == 200  # Re-renders form with error
    assert "Custom prompt must be 8000 characters or less" in response.text
    assert long_prompt in response.text  # Preserves content on validation error


@patch('app.routes.tenants.get_tenant_by_id')
def test_update_prompt_tenant_not_found(mock_get_tenant):
    """Test update prompt with non-existent tenant."""
    mock_get_tenant.return_value = None
    
    response = client.post("/tenants/999/prompt", data={"custom_prompt": "Test prompt"})
    
    assert response.status_code == 404


def test_tenants_list_shows_custom_prompt_badge():
    """Test that tenants list shows badge when custom prompt is set."""
    with patch('app.routes.tenants.list_tenants') as mock_list_tenants:
        mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant", custom_prompt="Custom prompt")
        mock_list_tenants.return_value = ([mock_tenant], 1)
        
        response = client.get("/tenants/")
        
        assert response.status_code == 200
        assert "Custom Prompt" in response.text
        assert "bg-warning" in response.text  # Bootstrap warning badge class


def test_tenants_list_no_badge_without_custom_prompt():
    """Test that tenants list doesn't show badge when no custom prompt."""
    with patch('app.routes.tenants.list_tenants') as mock_list_tenants:
        mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant", custom_prompt=None)
        mock_list_tenants.return_value = ([mock_tenant], 1)
        
        response = client.get("/tenants/")
        
        assert response.status_code == 200
        assert "Custom Prompt" not in response.text
        assert "bg-warning" not in response.text
