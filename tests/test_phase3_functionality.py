"""
Test Phase 3 functionality - admin UI and CSV operations.
"""

import pytest
import tempfile
import os
from pathlib import Path
from sqlmodel import Session
from app.db import get_engine, create_all_tables
from app.repos.tenants import create_tenant
from app.repos.products import create_product
from app.utils.csv_utils import generate_csv_template, parse_csv_file, import_products_from_csv


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        db_path = tmp.name
    
    # Set environment variable for the test
    original_db_url = os.environ.get("DB_URL")
    os.environ["DB_URL"] = f"sqlite:///{db_path}"
    
    try:
        # Create tables
        create_all_tables()
        yield db_path
    finally:
        # Cleanup
        os.unlink(db_path)
        if original_db_url:
            os.environ["DB_URL"] = original_db_url
        else:
            del os.environ["DB_URL"]


def test_csv_template_generation():
    """Test that CSV template has correct headers."""
    csv_content = generate_csv_template()
    
    expected_headers = [
        'tenant_slug', 'product_name', 'description', 'price_cpm', 
        'delivery_type', 'formats_json', 'targeting_json'
    ]
    
    # Check that all expected headers are present
    for header in expected_headers:
        assert header in csv_content


def test_csv_import_workflow(temp_db):
    """Test complete CSV import workflow."""
    engine = get_engine()
    with Session(engine) as session:
        # Create a test tenant
        tenant = create_tenant(session, "Test Publisher", "test-publisher")
        
        # Create CSV content
        csv_content = f"""tenant_slug,product_name,description,price_cpm,delivery_type,formats_json,targeting_json
test-publisher,Test Product,Test Description,10.50,guaranteed,"{{""sizes"": [""300x250""]}}","{{""geo"": [""US""]}}"
"""
        
        # Parse and import
        valid_rows, invalid_rows, parse_errors = parse_csv_file(csv_content.encode('utf-8'))
        imported_count, import_errors = import_products_from_csv(session, valid_rows)
        
        # Verify results
        assert len(parse_errors) == 0
        assert len(invalid_rows) == 0
        assert len(valid_rows) == 1
        assert imported_count == 1
        assert len(import_errors) == 0


def test_tenant_product_relationship(temp_db):
    """Test that tenant-product relationships work correctly."""
    engine = get_engine()
    with Session(engine) as session:
        # Create tenant
        tenant = create_tenant(session, "Test Publisher", "test-publisher")
        
        # Create product
        product = create_product(
            session, tenant.id, "Test Product", "Test Description", 
            10.50, "guaranteed", '{"sizes": ["300x250"]}', '{"geo": ["US"]}'
        )
        
        # Verify relationship
        assert product.tenant_id == tenant.id
        assert product.name == "Test Product"
        assert product.price_cpm == 10.50

