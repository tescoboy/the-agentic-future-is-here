from app.main import app
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

client = TestClient(app)

# Test if the route is being called at all
print("Testing route registration...")
print(f"Available routes with 'tenants': {[f'{route.methods} {route.path}' for route in app.routes if 'tenants' in route.path]}")

# Test a simple route first
print("\nTesting simple route...")
response = client.get("/tenants/")
print(f"Simple route status: {response.status_code}")

# Test the prompt route with full mocking
print("\nTesting prompt route with full mocking...")
with patch('app.db.get_session') as mock_db_session, \
     patch('app.routes.tenants.prompt.get_tenant_by_id') as mock_get_tenant, \
     patch('app.services.sales_contract.get_default_sales_prompt') as mock_default_prompt:
    
    # Mock the database session
    session = MagicMock()
    mock_db_session.return_value = session
    
    # Mock the tenant
    mock_tenant = MagicMock()
    mock_tenant.id = 1
    mock_tenant.name = "Test Tenant"
    mock_tenant.slug = "test-tenant"
    mock_tenant.custom_prompt = "Custom prompt text"
    mock_get_tenant.return_value = mock_tenant
    
    # Mock the default prompt
    mock_default_prompt.return_value = "Default prompt text"
    
    response = client.get("/tenants/1/prompt")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    print(f"DB session mock called: {mock_db_session.called}")
    print(f"Get tenant mock called: {mock_get_tenant.called}")
    print(f"Default prompt mock called: {mock_default_prompt.called}")
