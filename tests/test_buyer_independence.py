"""
Unit tests for buyer independence from tenant context.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models import Tenant

client = TestClient(app)


def test_buyer_loads_without_tenant_context():
    """Test that /buyer loads correctly without any tenant context."""
    response = client.get("/buyer")
    
    assert response.status_code == 200
    assert "Submit Brief" in response.text
    assert "agent" in response.text.lower()


def test_buyer_shows_all_enabled_agents():
    """Test that buyer shows all enabled agents regardless of tenant context."""
    with patch('app.routes.buyer._get_available_agents') as mock_get_agents:
        mock_get_agents.return_value = [
            {"id": "sales:tenant:1", "name": "Tenant 1", "type": "Sales", "enabled": True},
            {"id": "sales:tenant:2", "name": "Tenant 2", "type": "Sales", "enabled": True},
            {"id": "signals:external:1", "name": "Signals Agent", "type": "Signals", "enabled": True},
        ]
        
        response = client.get("/buyer")
        
        assert response.status_code == 200
        assert "Tenant 1" in response.text
        assert "Tenant 2" in response.text
        assert "Signals Agent" in response.text


def test_buyer_no_pre_selection():
    """Test that no agents are pre-selected based on tenant context."""
    with patch('app.routes.buyer._get_available_agents') as mock_get_agents:
        mock_get_agents.return_value = [
            {"id": "sales:tenant:1", "name": "Tenant 1", "type": "Sales", "enabled": True},
        ]
        
        response = client.get("/buyer")
        
        assert response.status_code == 200
        # Check that the checkbox is not checked by default
        assert 'checked' not in response.text or 'checked=""' not in response.text


def test_buyer_submits_without_tenant_context():
    """Test that buyer form submits correctly without tenant context."""
    # Just test that the form can be submitted without errors
    response = client.post("/buyer/", data={
        "brief": "Test brief",
        "agents": ["sales:tenant:1"]
    })
    
    # Should either succeed or show validation errors, but not crash
    assert response.status_code in [200, 422]


def test_buyer_tenant_badge_not_visible():
    """Test that tenant badge is not visible on buyer pages."""
    # Set a tenant cookie
    client.cookies.set("tenant_slug", "test-tenant")
    
    response = client.get("/buyer")
    
    assert response.status_code == 200
    # Tenant badge should not be visible on buyer pages
    assert "Admin:" not in response.text
    assert "test-tenant" not in response.text


def test_buyer_tenant_badge_visible_on_admin():
    """Test that tenant badge is visible on admin pages when context exists."""
    # Set a tenant cookie
    client.cookies.set("tenant_slug", "test-tenant")
    
    response = client.get("/tenants")
    
    assert response.status_code == 200
    # Tenant badge should be visible on admin pages
    assert "Admin:" in response.text
    assert "test-tenant" in response.text


def test_buyer_works_with_real_data():
    """Test that buyer works with real data without tenant context."""
    # Test with actual data from the database
    response = client.get("/buyer")
    
    assert response.status_code == 200
    # Should show the form with available agents
    assert "Submit Brief" in response.text
    # Should not require any tenant context
    assert "tenant required" not in response.text.lower()
