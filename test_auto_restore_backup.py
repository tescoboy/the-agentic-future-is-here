#!/usr/bin/env python3
"""
Test script to verify auto-restore and backup functionality.
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.db import get_session
from app.models import Tenant, Product, ExternalAgent
from app.utils.data_persistence.backup import auto_restore_on_startup, create_backup
from app.utils.data_persistence.export import export_all_data
from sqlmodel import select

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_backup_restore():
    """Test the backup and restore functionality."""
    
    session = next(get_session())
    
    try:
        # Step 1: Check current database state
        logger.info("=== Step 1: Checking current database state ===")
        tenant_count = len(session.exec(select(Tenant)).all())
        product_count = len(session.exec(select(Product)).all())
        agent_count = len(session.exec(select(ExternalAgent)).all())
        
        logger.info(f"Current database: {tenant_count} tenants, {product_count} products, {agent_count} agents")
        
        # Step 2: Create a test tenant with custom settings
        logger.info("=== Step 2: Creating test tenant with custom settings ===")
        
        # Check if test tenant exists
        test_tenant = session.exec(select(Tenant).where(Tenant.slug == "test-backup")).first()
        
        if not test_tenant:
            test_tenant = Tenant(
                name="Test Backup Tenant",
                slug="test-backup",
                custom_prompt="This is a test custom prompt for backup testing",
                web_grounding_prompt="This is a test web grounding prompt for backup testing",
                enable_web_context=True
            )
            session.add(test_tenant)
            session.commit()
            logger.info("Created test tenant with custom settings")
        else:
            # Update existing test tenant
            test_tenant.custom_prompt = "This is a test custom prompt for backup testing"
            test_tenant.web_grounding_prompt = "This is a test web grounding prompt for backup testing"
            test_tenant.enable_web_context = True
            session.add(test_tenant)
            session.commit()
            logger.info("Updated existing test tenant with custom settings")
        
        # Step 3: Create a backup
        logger.info("=== Step 3: Creating backup ===")
        backup_result = create_backup()
        logger.info(f"Backup result: {backup_result}")
        
        # Step 4: Export data to verify what's in the backup
        logger.info("=== Step 4: Exporting data to verify backup contents ===")
        backup_data = export_all_data(session)
        
        # Check if our test tenant settings are in the backup
        test_tenant_backup = None
        for tenant in backup_data.get("tenants", []):
            if tenant["slug"] == "test-backup":
                test_tenant_backup = tenant
                break
        
        if test_tenant_backup:
            logger.info("✓ Test tenant found in backup")
            logger.info(f"  - custom_prompt: {test_tenant_backup.get('custom_prompt', 'NOT FOUND')}")
            logger.info(f"  - web_grounding_prompt: {test_tenant_backup.get('web_grounding_prompt', 'NOT FOUND')}")
            logger.info(f"  - enable_web_context: {test_tenant_backup.get('enable_web_context', 'NOT FOUND')}")
        else:
            logger.error("✗ Test tenant not found in backup")
        
        # Step 5: Clear the database (simulate empty database on restart)
        logger.info("=== Step 5: Clearing database to simulate restart ===")
        session.exec(select(Product)).delete()
        session.exec(select(ExternalAgent)).delete()
        session.exec(select(Tenant)).delete()
        session.commit()
        
        # Verify database is empty
        tenant_count = len(session.exec(select(Tenant)).all())
        product_count = len(session.exec(select(Product)).all())
        agent_count = len(session.exec(select(ExternalAgent)).all())
        logger.info(f"Database cleared: {tenant_count} tenants, {product_count} products, {agent_count} agents")
        
        # Step 6: Test auto-restore
        logger.info("=== Step 6: Testing auto-restore ===")
        auto_restore_on_startup(session)
        
        # Step 7: Verify restore worked
        logger.info("=== Step 7: Verifying restore results ===")
        tenant_count = len(session.exec(select(Tenant)).all())
        product_count = len(session.exec(select(Product)).all())
        agent_count = len(session.exec(select(ExternalAgent)).all())
        
        logger.info(f"After restore: {tenant_count} tenants, {product_count} products, {agent_count} agents")
        
        # Check if our test tenant was restored with correct settings
        restored_tenant = session.exec(select(Tenant).where(Tenant.slug == "test-backup")).first()
        
        if restored_tenant:
            logger.info("✓ Test tenant restored successfully")
            logger.info(f"  - custom_prompt: {restored_tenant.custom_prompt}")
            logger.info(f"  - web_grounding_prompt: {restored_tenant.web_grounding_prompt}")
            logger.info(f"  - enable_web_context: {restored_tenant.enable_web_context}")
            
            # Verify settings were restored correctly
            if (restored_tenant.custom_prompt == "This is a test custom prompt for backup testing" and
                restored_tenant.web_grounding_prompt == "This is a test web grounding prompt for backup testing" and
                restored_tenant.enable_web_context == True):
                logger.info("✓ All tenant settings restored correctly!")
                return True
            else:
                logger.error("✗ Tenant settings not restored correctly")
                return False
        else:
            logger.error("✗ Test tenant not restored")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    success = test_backup_restore()
    if success:
        logger.info("🎉 All tests passed! Auto-restore and backup functionality is working correctly.")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed! Auto-restore and backup functionality has issues.")
        sys.exit(1)
