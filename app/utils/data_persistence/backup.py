"""
Backup and restore functions for data persistence.
"""

import logging
import os
from typing import List, Optional
from sqlmodel import Session
from datetime import datetime

from .export import export_all_data
from .import_utils import import_all_data
from .core import ensure_data_directories, BACKUP_DIR

logger = logging.getLogger(__name__)


def create_backup() -> str:
    """Create a backup of all data."""
    from app.db import get_session
    
    session = next(get_session())
    try:
        backup_data = export_all_data(session)
        return "Backup created successfully"
    finally:
        session.close()


def restore_backup(backup_file: Optional[str] = None) -> str:
    """Restore data from backup."""
    from app.db import get_session
    
    session = next(get_session())
    try:
        import_all_data(session, backup_file=backup_file)
        return "Backup restored successfully"
    finally:
        session.close()


def list_backups() -> List[str]:
    """List all available backup files."""
    ensure_data_directories()
    # Include both compressed (.json.gz) and uncompressed (.json) backup files
    json_files = list(BACKUP_DIR.glob("full_backup_*.json"))
    gz_files = list(BACKUP_DIR.glob("full_backup_*.json.gz"))
    backup_files = json_files + gz_files
    return [f.name for f in sorted(backup_files, key=os.path.getctime, reverse=True)]


def auto_backup_on_startup(session: Session) -> None:
    """Automatically create a backup on startup."""
    try:
        # Check if database has data before creating backup
        from app.models import Tenant, Product, ExternalAgent
        from sqlmodel import select
        
        tenant_count = len(session.exec(select(Tenant)).all())
        product_count = len(session.exec(select(Product)).all())
        agent_count = len(session.exec(select(ExternalAgent)).all())
        
        total_records = tenant_count + product_count + agent_count
        
        # Debug: Log detailed database state
        logger.info(f"BACKUP_DEBUG: Database state check:")
        logger.info(f"BACKUP_DEBUG:   - Tenants: {tenant_count}")
        logger.info(f"BACKUP_DEBUG:   - Products: {product_count}")
        logger.info(f"BACKUP_DEBUG:   - External Agents: {agent_count}")
        logger.info(f"BACKUP_DEBUG:   - Total Records: {total_records}")
        
        if total_records > 0:
            export_all_data(session)
            logger.info("Auto-backup created on startup")
        else:
            logger.info("Database is empty, skipping auto-backup")
    except Exception as e:
        logger.warning(f"Auto-backup failed: {e}")


def auto_restore_on_startup(session: Session) -> None:
    """Automatically restore from latest backup on startup if database is empty."""
    try:
        # Check if database is empty
        from app.models import Tenant, Product, ExternalAgent
        from sqlmodel import select
        
        tenant_count = len(session.exec(select(Tenant)).all())
        product_count = len(session.exec(select(Product)).all())
        agent_count = len(session.exec(select(ExternalAgent)).all())
        
        total_records = tenant_count + product_count + agent_count
        
        # Debug: Log detailed database state
        logger.info(f"RESTORE_DEBUG: Database state check:")
        logger.info(f"RESTORE_DEBUG:   - Tenants: {tenant_count}")
        logger.info(f"RESTORE_DEBUG:   - Products: {product_count}")
        logger.info(f"RESTORE_DEBUG:   - External Agents: {agent_count}")
        logger.info(f"RESTORE_DEBUG:   - Total Records: {total_records}")
        
        if total_records > 0:
            logger.info(f"Database not empty ({total_records} records), skipping auto-restore")
            return
        
        # Database is empty, check for backup files (include both .json and .json.gz)
        json_files = list(BACKUP_DIR.glob("full_backup_*.json"))
        gz_files = list(BACKUP_DIR.glob("full_backup_*.json.gz"))
        backup_files = json_files + gz_files
        
        # Debug: Log backup files found
        logger.info(f"RESTORE_DEBUG: Backup files found: {len(backup_files)}")
        for backup_file in backup_files:
            logger.info(f"RESTORE_DEBUG:   - {backup_file.name}")
        
        # Debug: Also check what files exist in the backup directory
        all_files = list(BACKUP_DIR.glob("*"))
        logger.info(f"RESTORE_DEBUG: All files in backup directory: {len(all_files)}")
        for file in all_files:
            logger.info(f"RESTORE_DEBUG:   - {file.name}")
        
        if backup_files:
            latest_backup = max(backup_files, key=os.path.getctime)
            logger.info(f"Database is empty, auto-restoring from: {latest_backup.name}")
            import_all_data(session, backup_file=latest_backup.name)
            logger.info(f"Auto-restore completed successfully from: {latest_backup.name}")
        else:
            logger.info("Database is empty but no backup files found for auto-restore")
    except Exception as e:
        logger.warning(f"Auto-restore failed: {e}")


def test_persistent_disk() -> str:
    """Test if the persistent disk is working by writing and reading a test file."""
    try:
        ensure_data_directories()
        
        # Write a test file
        test_file = BACKUP_DIR / "disk_test.txt"
        test_content = f"Disk test at {datetime.now().isoformat()}"
        
        logger.info(f"DISK_TEST: Writing test file to {test_file}")
        test_file.write_text(test_content)
        
        # Verify file was written
        if test_file.exists():
            file_size = test_file.stat().st_size
            logger.info(f"DISK_TEST: Test file created successfully (size: {file_size} bytes)")
            
            # Read the file back
            read_content = test_file.read_text()
            if read_content == test_content:
                logger.info("DISK_TEST: File read/write test PASSED")
                return f"Persistent disk test PASSED - file written and read successfully (size: {file_size} bytes)"
            else:
                logger.error("DISK_TEST: File content mismatch")
                return "Persistent disk test FAILED - file content mismatch"
        else:
            logger.error("DISK_TEST: Test file was not created")
            return "Persistent disk test FAILED - file not created"
            
    except Exception as e:
        logger.error(f"DISK_TEST: Test failed with error: {e}")
        import traceback
        logger.error(f"DISK_TEST: Traceback: {traceback.format_exc()}")
        return f"Persistent disk test FAILED - {str(e)}"
