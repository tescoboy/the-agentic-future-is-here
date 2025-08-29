"""
Backup and restore functions for data persistence.
"""

import logging
import os
from typing import List, Optional
from sqlalchemy.orm import Session

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
    backup_files = list(BACKUP_DIR.glob("full_backup_*.json"))
    return [f.name for f in sorted(backup_files, key=os.path.getctime, reverse=True)]


def auto_backup_on_startup(session: Session) -> None:
    """Automatically create a backup on startup."""
    try:
        export_all_data(session)
        logger.info("Auto-backup created on startup")
    except Exception as e:
        logger.warning(f"Auto-backup failed: {e}")


def auto_restore_on_startup(session: Session) -> None:
    """Automatically restore from latest backup on startup."""
    try:
        backup_files = list(BACKUP_DIR.glob("full_backup_*.json"))
        if backup_files:
            latest_backup = max(backup_files, key=os.path.getctime)
            import_all_data(session, backup_file=str(latest_backup))
            logger.info(f"Auto-restored from: {latest_backup.name}")
        else:
            logger.info("No backup files found for auto-restore")
    except Exception as e:
        logger.warning(f"Auto-restore failed: {e}")
