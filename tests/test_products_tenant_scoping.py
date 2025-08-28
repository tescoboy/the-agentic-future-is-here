"""
Unit tests for products tenant scoping in admin context.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models import Tenant

client = TestClient(app)


def test_products_create_respects_tenant_context():
    """Test that product create respects tenant context when set."""
    # Set tenant context
    client.cookies.set("tenant_slug", "test-tenant")
    
    with patch('app.routes.products_routes.crud.get_current_tenant') as mock_get_tenant:
        mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant")
        mock_get_tenant.return_value = mock_tenant
        
        # Try to create product with different tenant ID
        response = client.post("/products/", data={
            "tenant_id": "2",  # Different tenant
            "name": "Test Product",
            "price_cpm": "10.0",
            "delivery_type": "banner"
        })
        
        assert response.status_code == 200
        assert "Tenant mismatch" in response.text
        assert "form specifies tenant 2 but current context is tenant 1" in response.text


def test_products_create_allows_correct_tenant():
    """Test that product create allows correct tenant ID when context is set."""
    # Set tenant context
    client.cookies.set("tenant_slug", "test-tenant")
    
    with patch('app.routes.products_routes.crud.get_current_tenant') as mock_get_tenant:
        mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant")
        mock_get_tenant.return_value = mock_tenant
        
        # Create product with correct tenant ID - should not show tenant mismatch error
        response = client.post("/products/", data={
            "tenant_id": "1",  # Correct tenant
            "name": "Test Product",
            "price_cpm": "10.0",
            "delivery_type": "banner"
        })
        
        # Should not show tenant mismatch error
        assert "Tenant mismatch" not in response.text


def test_products_create_no_context_allows_any_tenant():
    """Test that product create allows any tenant when no context is set."""
    with patch('app.routes.products_routes.crud.get_current_tenant') as mock_get_tenant:
        mock_get_tenant.return_value = None  # No tenant context
        
        # Create product with a valid tenant ID - should not show tenant mismatch error
        response = client.post("/products/", data={
            "tenant_id": "1",  # Use a valid tenant ID
            "name": "Test Product",
            "price_cpm": "10.0",
            "delivery_type": "banner"
        })
        
        # Should not show tenant mismatch error
        assert "Tenant mismatch" not in response.text


def test_products_update_respects_tenant_context():
    """Test that product update respects tenant context when set."""
    # Set tenant context
    client.cookies.set("tenant_slug", "test-tenant")
    
    with patch('app.routes.products_routes.crud.get_current_tenant') as mock_get_tenant:
        mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant")
        mock_get_tenant.return_value = mock_tenant
        
        with patch('app.routes.products_routes.crud.get_product_by_id') as mock_get_product:
            mock_product = MagicMock()
            mock_get_product.return_value = mock_product
            
            # Try to update product with different tenant ID
            response = client.post("/products/1/edit", data={
                "tenant_id": "2",  # Different tenant
                "name": "Test Product",
                "price_cpm": "10.0",
                "delivery_type": "banner"
            })
            
            assert response.status_code == 200
            assert "Tenant mismatch" in response.text
            assert "form specifies tenant 2 but current context is tenant 1" in response.text


def test_products_update_allows_correct_tenant():
    """Test that product update allows correct tenant ID when context is set."""
    # Set tenant context
    client.cookies.set("tenant_slug", "test-tenant")
    
    with patch('app.routes.products_routes.crud.get_current_tenant') as mock_get_tenant:
        mock_tenant = Tenant(id=1, name="Test Tenant", slug="test-tenant")
        mock_get_tenant.return_value = mock_tenant
        
        with patch('app.routes.products_routes.crud.get_product_by_id') as mock_get_product:
            mock_product = MagicMock()
            mock_get_product.return_value = mock_product
            
            # Update product with correct tenant ID - should not show tenant mismatch error
            response = client.post("/products/1/edit", data={
                "tenant_id": "1",  # Correct tenant
                "name": "Test Product",
                "price_cpm": "10.0",
                "delivery_type": "banner"
            })
            
            # Should not show tenant mismatch error
            assert "Tenant mismatch" not in response.text
