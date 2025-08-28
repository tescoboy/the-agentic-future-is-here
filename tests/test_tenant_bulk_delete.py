"""
Tests for bulk delete all tenants functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestBulkDeleteAllTenants:
    """Test bulk delete all tenants functionality."""
    
    def test_bulk_delete_all_tenants_route_exists(self):
        """Test that the bulk delete route exists."""
        response = client.post("/tenants/delete-all", follow_redirects=False)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response text: {response.text[:500]}")  # First 500 chars
        # Should redirect back to /tenants
        assert response.status_code == 302
        assert response.headers["location"] == "/tenants"
    
    def test_bulk_delete_all_tenants_route_with_mock(self):
        """Test bulk delete route with mocked database."""
        with patch('app.routes.tenants.bulk_delete_all_tenants') as mock_bulk_delete:
            mock_bulk_delete.return_value = 3  # Assume 3 tenants were deleted
            
            response = client.post("/tenants/delete-all", follow_redirects=False)
            
            assert response.status_code == 302
            assert response.headers["location"] == "/tenants"
            mock_bulk_delete.assert_called_once()
    
    def test_bulk_delete_all_tenants_repository_function(self):
        """Test the repository function directly."""
        from app.repos.tenants import bulk_delete_all_tenants
        
        # Test the function with a proper mock session
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []  # No tenants to delete
        
        result = bulk_delete_all_tenants(mock_session)
        
        assert result == 0
        mock_session.commit.assert_called_once()
    
    def test_tenants_index_shows_delete_all_button_when_tenants_exist(self):
        """Test that the delete all button appears when tenants exist."""
        with patch('app.routes.tenants.list_tenants') as mock_list_tenants:
            # Mock some tenants
            mock_tenant = MagicMock()
            mock_tenant.id = 1
            mock_tenant.name = "Test Tenant"
            mock_tenant.slug = "test"
            mock_tenant.created_at = MagicMock()
            mock_tenant.created_at.strftime.return_value = "2024-01-01 12:00"
            mock_tenant.custom_prompt = None
            
            mock_list_tenants.return_value = ([mock_tenant], 1)
            
            response = client.get("/tenants")
            
            assert response.status_code == 200
            assert "Delete All Tenants" in response.text
            assert 'action="/tenants/delete-all"' in response.text
    
    def test_tenants_index_hides_delete_all_button_when_no_tenants(self):
        """Test that the delete all button is hidden when no tenants exist."""
        with patch('app.routes.tenants.list_tenants') as mock_list_tenants:
            mock_list_tenants.return_value = ([], 0)
            
            response = client.get("/tenants")
            
            assert response.status_code == 200
            assert "Delete All Tenants" not in response.text
            assert 'action="/tenants/delete-all"' not in response.text
