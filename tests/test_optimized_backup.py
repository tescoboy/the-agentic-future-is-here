"""
Comprehensive tests for the optimized backup and restore system.
Tests all functionality including validation and error handling.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
from sqlmodel import Session, create_engine, SQLModel

from app.models import Tenant, Product, ExternalAgent
from app.utils.data_persistence.optimized_backup import OptimizedBackupManager


class TestOptimizedBackup:
    """Test suite for optimized backup system."""
    
    @pytest.fixture(scope="function")
    def test_session(self):
        """Create a test database session."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        SQLModel.metadata.create_all(engine)
        
        session = Session(engine)
        yield session
        session.close()
    
    @pytest.fixture
    def sample_data(self, test_session: Session):
        """Create sample data for testing."""
        # Create tenants
        tenants = [
            Tenant(
                id=1,
                name="Test Tenant 1",
                slug="test-tenant-1",
                custom_prompt="Test prompt 1",
                enable_web_context=True
            ),
            Tenant(
                id=2,
                name="Test Tenant 2",
                slug="test-tenant-2",
                custom_prompt="Test prompt 2",
                enable_web_context=False
            )
        ]
        
        for tenant in tenants:
            test_session.add(tenant)
        
        # Create products
        products = [
            Product(
                id=1,
                tenant_id=1,
                name="Test Product 1",
                description="Description 1",
                price_cpm=10.50,
                delivery_type="guaranteed",
                formats_json='["video", "display"]',
                targeting_json='{"age": [25, 45]}'
            ),
            Product(
                id=2,
                tenant_id=1,
                name="Test Product 2",
                description="Description 2",
                price_cpm=15.75,
                delivery_type="non_guaranteed",
                formats_json='["banner"]',
                targeting_json='{"location": ["US", "CA"]}'
            ),
            Product(
                id=3,
                tenant_id=2,
                name="Test Product 3",
                description="Description 3",
                price_cpm=8.25,
                delivery_type="guaranteed",
                formats_json='["native"]',
                targeting_json='{"device": ["mobile"]}'
            )
        ]
        
        for product in products:
            test_session.add(product)
        
        # Create external agents
        agents = [
            ExternalAgent(
                id=1,
                name="Test Agent 1",
                base_url="http://test1.example.com",
                enabled=True,
                agent_type="sales",
                protocol="rest"
            ),
            ExternalAgent(
                id=2,
                name="Test Agent 2",
                base_url="http://test2.example.com",
                enabled=False,
                agent_type="signals",
                protocol="mcp"
            )
        ]
        
        for agent in agents:
            test_session.add(agent)
        
        test_session.commit()
        
        return {
            "tenants": tenants,
            "products": products,
            "external_agents": agents
        }
    
    @pytest.mark.asyncio
    async def test_comprehensive_backup_creation(self, test_session: Session, sample_data):
        """Test creating a comprehensive backup."""
        manager = OptimizedBackupManager(test_session)
        
        # Create backup
        backup_data = await manager.create_comprehensive_backup(use_compression=False)
        
        # Verify backup structure
        assert "backup_metadata" in backup_data
        assert "tenants" in backup_data
        assert "products" in backup_data
        assert "external_agents" in backup_data
        assert "app_settings" in backup_data
        assert "tenant_settings" in backup_data
        
        # Verify data counts
        metadata = backup_data["backup_metadata"]
        data_counts = metadata["data_counts"]
        
        assert data_counts["tenants"] == 2
        assert data_counts["products"] == 3
        assert data_counts["external_agents"] == 2
        
        # Verify tenant data
        tenants = backup_data["tenants"]
        assert len(tenants) == 2
        assert tenants[0]["name"] == "Test Tenant 1"
        assert tenants[0]["enable_web_context"] is True
        assert tenants[1]["enable_web_context"] is False
        
        # Verify product data
        products = backup_data["products"]
        assert len(products) == 3
        assert products[0]["price_cpm"] == 10.50
        assert products[1]["tenant_id"] == 1
        assert products[2]["tenant_id"] == 2
        
        # Verify external agent data
        agents = backup_data["external_agents"]
        assert len(agents) == 2
        assert agents[0]["enabled"] is True
        assert agents[1]["enabled"] is False
    
    @pytest.mark.asyncio
    async def test_backup_validation(self, test_session: Session, sample_data):
        """Test backup validation functionality."""
        manager = OptimizedBackupManager(test_session)
        
        # Create valid backup
        backup_data = await manager.create_comprehensive_backup(use_compression=False)
        
        # Test valid backup
        validation_result = await manager._validate_backup_integrity(backup_data)
        assert validation_result["valid"] is True
        assert len(validation_result["errors"]) == 0
        
        # Test invalid backup - missing required section
        invalid_backup = backup_data.copy()
        del invalid_backup["tenants"]
        
        validation_result = await manager._validate_backup_integrity(invalid_backup)
        assert validation_result["valid"] is False
        assert any("Missing required section: tenants" in error for error in validation_result["errors"])
        
        # Test backup with orphaned products
        invalid_backup = backup_data.copy()
        invalid_backup["products"] = [
            {
                "id": 999,
                "tenant_id": 999,  # Non-existent tenant
                "name": "Orphaned Product",
                "price_cpm": 10.0
            }
        ]
        
        validation_result = await manager._validate_backup_integrity(invalid_backup)
        assert len(validation_result["warnings"]) > 0
        assert any("missing tenants" in warning for warning in validation_result["warnings"])
    
    @pytest.mark.asyncio
    async def test_comprehensive_restore(self, test_session: Session, sample_data):
        """Test comprehensive backup restore."""
        manager = OptimizedBackupManager(test_session)
        
        # Create backup
        backup_data = await manager.create_comprehensive_backup(use_compression=False)
        
        # Clear existing data
        await manager._clear_existing_data()
        
        # Verify data is cleared
        from sqlmodel import text
        tenant_count = test_session.execute(text("SELECT COUNT(*) FROM tenant")).scalar()
        product_count = test_session.execute(text("SELECT COUNT(*) FROM product")).scalar()
        agent_count = test_session.execute(text("SELECT COUNT(*) FROM externalagent")).scalar()
        
        assert tenant_count == 0
        assert product_count == 0
        assert agent_count == 0
        
        # Restore backup
        validation_result = await manager.restore_comprehensive_backup(
            backup_data=backup_data,
            validate_before_restore=True
        )
        
        # Verify restoration
        assert validation_result["counts_match"] is True
        assert validation_result["tenants_restored"] == 2
        assert validation_result["products_restored"] == 3
        assert validation_result["external_agents_restored"] == 2
        
        # Verify data integrity
        tenant_count = test_session.execute(text("SELECT COUNT(*) FROM tenant")).scalar()
        product_count = test_session.execute(text("SELECT COUNT(*) FROM product")).scalar()
        agent_count = test_session.execute(text("SELECT COUNT(*) FROM externalagent")).scalar()
        
        assert tenant_count == 2
        assert product_count == 3
        assert agent_count == 2
        
        # Verify specific data
        tenant = test_session.execute(text("SELECT * FROM tenant WHERE id = 1")).first()
        assert tenant.name == "Test Tenant 1"
        assert tenant.slug == "test-tenant-1"
        assert bool(tenant.enable_web_context) is True
        
        product = test_session.execute(text("SELECT * FROM product WHERE id = 1")).first()
        assert product.name == "Test Product 1"
        assert product.tenant_id == 1
        assert product.price_cpm == 10.50
    
    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, test_session: Session):
        """Test performance of bulk operations with larger datasets."""
        # Create larger dataset
        large_tenants = []
        large_products = []
        
        for i in range(10):
            tenant = Tenant(
                id=i + 1,
                name=f"Tenant {i + 1}",
                slug=f"tenant-{i + 1}",
                custom_prompt=f"Prompt {i + 1}",
                enable_web_context=(i % 2 == 0)
            )
            test_session.add(tenant)
            large_tenants.append(tenant)
        
        for i in range(100):
            product = Product(
                id=i + 1,
                tenant_id=(i % 10) + 1,
                name=f"Product {i + 1}",
                description=f"Description {i + 1}",
                price_cpm=float(10 + i),
                delivery_type="guaranteed" if i % 2 == 0 else "non_guaranteed",
                formats_json='["video", "display"]',
                targeting_json='{"age": [25, 45]}'
            )
            test_session.add(product)
            large_products.append(product)
        
        test_session.commit()
        
        # Test backup performance
        manager = OptimizedBackupManager(test_session)
        
        import time
        start_time = time.time()
        backup_data = await manager.create_comprehensive_backup(use_compression=False)
        backup_time = time.time() - start_time
        
        assert backup_time < 10.0  # Should complete within 10 seconds
        assert len(backup_data["tenants"]) == 10
        assert len(backup_data["products"]) == 100
        
        # Test restore performance
        await manager._clear_existing_data()
        
        start_time = time.time()
        await manager.restore_comprehensive_backup(backup_data=backup_data)
        restore_time = time.time() - start_time
        
        assert restore_time < 10.0  # Should complete within 10 seconds
        
        # Verify data
        from sqlmodel import text
        tenant_count = test_session.execute(text("SELECT COUNT(*) FROM tenant")).scalar()
        product_count = test_session.execute(text("SELECT COUNT(*) FROM product")).scalar()
        
        assert tenant_count == 10
        assert product_count == 100
    
    @pytest.mark.asyncio
    async def test_compressed_backup(self, test_session: Session, sample_data):
        """Test compressed backup functionality."""
        manager = OptimizedBackupManager(test_session)
        
        # Create compressed backup
        backup_data = await manager.create_comprehensive_backup(use_compression=True)
        
        # Verify backup can be restored
        await manager._clear_existing_data()
        validation_result = await manager.restore_comprehensive_backup(backup_data=backup_data)
        
        assert validation_result["counts_match"] is True
    
    @pytest.mark.asyncio
    async def test_settings_backup_restore(self, test_session: Session):
        """Test backup and restore of settings files."""
        manager = OptimizedBackupManager(test_session)
        
        # Mock environment variables
        original_env = os.environ.copy()
        os.environ.update({
            "GEMINI_API_KEY": "test-key-123",
            "EMBEDDINGS_PROVIDER": "gemini",
            "ENABLE_WEB_CONTEXT": "1",
            "DEBUG": "0"
        })
        
        try:
            # Create backup with settings
            backup_data = await manager.create_comprehensive_backup(use_compression=False)
            
            # Verify settings are in backup
            app_settings = backup_data["app_settings"]
            env_vars = app_settings["environment_variables"]
            
            assert env_vars["GEMINI_API_KEY"] == "test-key-123"
            assert env_vars["EMBEDDINGS_PROVIDER"] == "gemini"
            assert env_vars["ENABLE_WEB_CONTEXT"] == "1"
            
            # Test restore (settings files should be written)
            await manager._restore_app_settings(app_settings)
            
            # Verify feature flags
            feature_flags = backup_data["feature_flags"]
            assert feature_flags["web_context_enabled"] is True
            assert feature_flags["debug_mode"] is False
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, test_session: Session):
        """Test error handling in backup and restore operations."""
        manager = OptimizedBackupManager(test_session)
        
        # Test restore with non-existent file
        with pytest.raises(FileNotFoundError):
            await manager.restore_comprehensive_backup(backup_file="non_existent_file.json")
        
        # Test restore with invalid backup data
        invalid_backup = {"invalid": "data"}
        
        with pytest.raises(ValueError):
            await manager.restore_comprehensive_backup(
                backup_data=invalid_backup,
                validate_before_restore=True
            )
    
    def test_export_methods_individual(self, test_session: Session, sample_data):
        """Test individual export methods."""
        manager = OptimizedBackupManager(test_session)
        
        # Test tenant export
        tenants = manager._export_tenants_bulk()
        assert len(tenants) == 2
        assert tenants[0]["name"] == "Test Tenant 1"
        
        # Test product export
        products = manager._export_products_bulk()
        assert len(products) == 3
        assert products[0]["price_cpm"] == 10.50
        
        # Test external agent export
        agents = manager._export_external_agents_bulk()
        assert len(agents) == 2
        assert agents[0]["enabled"] is True
        
        # Test settings export
        app_settings = manager._export_app_settings_comprehensive()
        assert "environment_variables" in app_settings
        assert "export_timestamp" in app_settings
        
        tenant_settings = manager._export_tenant_settings_comprehensive()
        assert "export_timestamp" in tenant_settings
    
    def test_restore_methods_individual(self, test_session: Session, sample_data):
        """Test individual restore methods."""
        manager = OptimizedBackupManager(test_session)
        
        # Export data first
        tenants_data = manager._export_tenants_bulk()
        products_data = manager._export_products_bulk()
        agents_data = manager._export_external_agents_bulk()
        
        # Clear data
        from sqlmodel import text
        test_session.execute(text("DELETE FROM product"))
        test_session.execute(text("DELETE FROM externalagent"))
        test_session.execute(text("DELETE FROM tenant"))
        test_session.commit()
        
        # Test individual restore methods
        manager._restore_tenants_bulk(tenants_data)
        manager._restore_products_bulk(products_data)
        manager._restore_external_agents_bulk(agents_data)
        
        # Verify restoration
        tenant_count = test_session.execute(text("SELECT COUNT(*) FROM tenant")).scalar()
        product_count = test_session.execute(text("SELECT COUNT(*) FROM product")).scalar()
        agent_count = test_session.execute(text("SELECT COUNT(*) FROM externalagent")).scalar()
        
        assert tenant_count == 2
        assert product_count == 3
        assert agent_count == 2


# Integration test with file I/O
@pytest.mark.asyncio
async def test_full_backup_restore_workflow():
    """Test complete backup/restore workflow with file operations."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Setup test database
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        SQLModel.metadata.create_all(engine)
        
        session = Session(engine)
        
        # Add test data
        tenant = Tenant(id=1, name="Test Tenant", slug="test", custom_prompt="Test")
        product = Product(
            id=1, tenant_id=1, name="Test Product", description="Test",
            price_cpm=10.0, delivery_type="guaranteed"
        )
        
        session.add(tenant)
        session.add(product)
        session.commit()
        
        # Create backup manager
        manager = OptimizedBackupManager(session)
        
        # Create backup
        backup_data = await manager.create_comprehensive_backup(use_compression=True)
        
        # Clear database
        await manager._clear_existing_data()
        
        # Restore from backup
        validation_result = await manager.restore_comprehensive_backup(backup_data=backup_data)
        
        # Verify restoration
        assert validation_result["tenants_restored"] == 1
        assert validation_result["products_restored"] == 1
        assert validation_result["counts_match"] is True
        
        session.close()
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v"])
