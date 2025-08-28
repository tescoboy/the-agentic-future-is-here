"""
Unit tests for tenant context functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models import Tenant
from app.services.tenant_context import (
    get_current_tenant, set_current_tenant, clear_current_tenant,
    resolve_tenant, resolve_tenant_or_404
)

client = TestClient(app)


@patch('app.services.tenant_context.get_tenant_by_slug')
def test_get_current_tenant_with_context(mock_get_tenant):
    """Test getting current tenant when context exists."""
    mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant")
    mock_get_tenant.return_value = mock_tenant
    
    # Mock request with tenant context
    request = MagicMock()
    request.state.tenant = mock_tenant
    
    result = get_current_tenant(request)
    assert result == mock_tenant


def test_get_current_tenant_without_context():
    """Test getting current tenant when no context exists."""
    request = MagicMock()
    request.state.tenant = None
    
    result = get_current_tenant(request)
    assert result is None


def test_set_current_tenant_cookie():
    """Test setting tenant cookie."""
    request = MagicMock()
    request.url.scheme = "https"
    
    response = MagicMock()
    
    set_current_tenant(request, response, "test-tenant")
    
    # Verify cookie was set with correct parameters
    response.set_cookie.assert_called_once()
    call_args = response.set_cookie.call_args
    assert call_args[1]['key'] == "tenant_slug"
    assert call_args[1]['value'] == "test-tenant"
    assert call_args[1]['httponly'] is True
    assert call_args[1]['samesite'] == "lax"
    assert call_args[1]['secure'] is True
    assert call_args[1]['path'] == "/"


def test_clear_current_tenant_cookie():
    """Test clearing tenant cookie."""
    response = MagicMock()
    
    clear_current_tenant(response)
    
    response.delete_cookie.assert_called_once_with(
        key="tenant_slug",
        path="/"
    )


@patch('app.services.tenant_context.get_tenant_by_slug')
def test_resolve_tenant_success(mock_get_tenant):
    """Test resolving tenant successfully."""
    mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant")
    mock_get_tenant.return_value = mock_tenant
    
    result = resolve_tenant("test-tenant")
    assert result == mock_tenant


@patch('app.services.tenant_context.get_tenant_by_slug')
def test_resolve_tenant_not_found(mock_get_tenant):
    """Test resolving tenant that doesn't exist."""
    mock_get_tenant.return_value = None
    
    result = resolve_tenant("nonexistent")
    assert result is None


@patch('app.services.tenant_context.resolve_tenant')
def test_resolve_tenant_or_404_success(mock_resolve):
    """Test resolve_tenant_or_404 with existing tenant."""
    mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant")
    mock_resolve.return_value = mock_tenant
    
    result = resolve_tenant_or_404("test-tenant")
    assert result == mock_tenant


@patch('app.services.tenant_context.resolve_tenant')
def test_resolve_tenant_or_404_not_found(mock_resolve):
    """Test resolve_tenant_or_404 with non-existent tenant."""
    mock_resolve.return_value = None
    
    with pytest.raises(Exception) as exc_info:
        resolve_tenant_or_404("nonexistent")
    
    assert "tenant 'nonexistent' not found" in str(exc_info.value)


@patch('app.routes.tenant_switch.resolve_tenant_or_404')
def test_switch_tenant_sets_cookie(mock_resolve_tenant):
    """Test that POST /switch-tenant sets cookie correctly."""
    mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant")
    mock_resolve_tenant.return_value = mock_tenant
    
    response = client.post("/switch-tenant/", data={"tenant_slug": "test-tenant"}, follow_redirects=False)
    
    assert response.status_code == 302
    assert response.headers["location"] == "/buyer"
    assert "tenant_slug=test-tenant" in response.headers.get("set-cookie", "")


def test_buyer_independent_of_tenant_context():
    """Test that /buyer works without tenant context (new architecture)."""
    response = client.get("/buyer")
    
    assert response.status_code == 200
    assert "Submit Brief" in response.text


def test_switch_tenant_clear_removes_context():
    """Test that POST /switch-tenant/clear removes context."""
    response = client.post("/switch-tenant/clear", follow_redirects=False)
    
    assert response.status_code == 302
    assert response.headers["location"] == "/switch-tenant"
    # Check that cookie is cleared (expires in the past)
    set_cookie = response.headers.get("set-cookie", "")
    assert "Max-Age=0" in set_cookie

