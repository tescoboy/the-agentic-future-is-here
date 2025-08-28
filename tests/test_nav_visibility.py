"""Tests for navigation visibility and badge display."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app

client = TestClient(app)


def test_buyer_page_no_tenant_badge():
    """Test that buyer page does not show tenant badge."""
    response = client.get("/buyer")
    assert response.status_code == 200
    assert "Admin:" not in response.text
    assert "tenant_slug" not in response.text


def test_buyer_page_has_admin_and_publishers_links():
    """Test that buyer page has Admin and Publishers navigation links."""
    response = client.get("/buyer")
    assert response.status_code == 200
    assert "Admin" in response.text
    assert "Publishers" in response.text
    assert "/tenants" in response.text
    assert "/publishers" in response.text


def test_publishers_index_page():
    """Test publishers index page loads correctly."""
    with patch('app.routes.publishers.list_tenants', return_value=([], 0)):
        response = client.get("/publishers")
        assert response.status_code == 200
        assert "Publishers" in response.text


def test_publisher_pages_show_publisher_badge():
    """Test that publisher pages show publisher badge."""
    with patch('app.routes.publisher._get_tenant_or_404') as mock_get_tenant:
        mock_tenant = MagicMock()
        mock_tenant.name = "Test Publisher"
        mock_tenant.slug = "test-publisher"
        mock_tenant.id = 1
        mock_tenant.custom_prompt = None
        mock_get_tenant.return_value = mock_tenant
        
        with patch('app.routes.publisher.list_products', return_value=([], 0)):
            response = client.get("/publisher/test-publisher/")
            assert response.status_code == 200
            assert "Publisher: Test Publisher (test-publisher)" in response.text


def test_publisher_pages_show_publisher_nav():
    """Test that publisher pages show publisher navigation."""
    with patch('app.routes.publisher._get_tenant_or_404') as mock_get_tenant:
        mock_tenant = MagicMock()
        mock_tenant.name = "Test Publisher"
        mock_tenant.slug = "test-publisher"
        mock_tenant.id = 1
        mock_tenant.custom_prompt = None
        mock_get_tenant.return_value = mock_tenant
        
        with patch('app.routes.publisher.list_products', return_value=([], 0)):
            response = client.get("/publisher/test-publisher/")
            assert response.status_code == 200
            assert "Dashboard" in response.text
            assert "Products" in response.text
            assert "CSV Import" in response.text
            assert "Prompt" in response.text
            assert "Switch Publisher" in response.text


def test_publisher_pages_use_dark_navbar():
    """Test that publisher pages use navbar-dark bg-secondary."""
    with patch('app.routes.publisher._get_tenant_or_404') as mock_get_tenant:
        mock_tenant = MagicMock()
        mock_tenant.name = "Test Publisher"
        mock_tenant.slug = "test-publisher"
        mock_tenant.id = 1
        mock_tenant.custom_prompt = None
        mock_get_tenant.return_value = mock_tenant
        
        with patch('app.routes.publisher.list_products', return_value=([], 0)):
            response = client.get("/publisher/test-publisher/")
            assert response.status_code == 200
            assert 'navbar-dark bg-secondary' in response.text


def test_admin_pages_accessible_without_auth():
    """Test that admin pages are accessible without authentication."""
    response = client.get("/tenants")
    assert response.status_code == 200
    
    response = client.get("/external-agents")
    assert response.status_code == 200


def test_publisher_pages_accessible_without_auth():
    """Test that publisher pages are accessible without authentication."""
    with patch('app.routes.publisher._get_tenant_or_404') as mock_get_tenant:
        mock_tenant = MagicMock()
        mock_tenant.name = "Test Publisher"
        mock_tenant.slug = "test-publisher"
        mock_tenant.id = 1
        mock_tenant.custom_prompt = None
        mock_get_tenant.return_value = mock_tenant
        
        with patch('app.routes.publisher.list_products', return_value=([], 0)):
            response = client.get("/publisher/test-publisher/")
            assert response.status_code == 200


def test_publisher_404_for_invalid_slug():
    """Test that publisher pages return 404 for invalid slugs."""
    with patch('app.routes.publisher._get_tenant_or_404', side_effect=HTTPException(status_code=404, detail="tenant 'invalid' not found")):
        response = client.get("/publisher/invalid/")
        assert response.status_code == 404


def test_base_template_has_admin_and_publishers_menu():
    """Test that base template includes Admin and Publishers menu items."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Admin" in response.text
    assert "Publishers" in response.text
    assert "/tenants" in response.text
    assert "/publishers" in response.text


def test_publisher_pages_have_buyer_and_admin_links():
    """Test that publisher pages have links back to Buyer and Admin."""
    with patch('app.routes.publisher._get_tenant_or_404') as mock_get_tenant:
        mock_tenant = MagicMock()
        mock_tenant.name = "Test Publisher"
        mock_tenant.slug = "test-publisher"
        mock_tenant.id = 1
        mock_tenant.custom_prompt = None
        mock_get_tenant.return_value = mock_tenant
        
        with patch('app.routes.publisher.list_products', return_value=([], 0)):
            response = client.get("/publisher/test-publisher/")
            assert response.status_code == 200
            assert "/buyer" in response.text
            assert "/tenants" in response.text
            assert "Buyer" in response.text
            assert "Admin" in response.text
