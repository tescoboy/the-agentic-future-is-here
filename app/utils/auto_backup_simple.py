"""
Simple auto-backup system without circular imports.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Data directory for persistence files
DATA_DIR = Path("./data")
BACKUP_DIR = DATA_DIR / "backups"
MAX_BACKUPS = 20


def ensure_data_directories():
    """Ensure all data directories exist."""
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)


def auto_backup(session: Session, reason: str = "data_change") -> Optional[str]:
    """
    Create automatic backup and cleanup old backups.
    Returns backup filename if successful, None if failed.
    """
    try:
        ensure_data_directories()
        
        # Import here to avoid circular imports
        from app.utils.data_persistence import export_all_data
        
        # Create backup
        backup_data = export_all_data(session)
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"full_backup_{timestamp}.json"
        backup_path = BACKUP_DIR / backup_filename
        
        # Write backup data
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        # Cleanup old backups
        cleanup_old_backups()
        
        logger.info(f"Auto-backup created: {backup_filename} (reason: {reason})")
        return backup_filename
        
    except Exception as e:
        logger.error(f"Auto-backup failed: {e}")
        return None


def cleanup_old_backups() -> None:
    """Keep only the last MAX_BACKUPS files, delete older ones."""
    try:
        backup_files = list(BACKUP_DIR.glob("full_backup_*.json"))
        
        if len(backup_files) <= MAX_BACKUPS:
            return  # No cleanup needed
        
        # Sort by creation time (oldest first)
        sorted_files = sorted(backup_files, key=os.path.getctime)
        
        # Delete oldest files
        files_to_delete = sorted_files[:-MAX_BACKUPS]
        
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                logger.info(f"Deleted old backup: {file_path.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {file_path.name}: {e}")
        
        logger.info(f"Cleanup completed: deleted {len(files_to_delete)} old backups")
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")


def get_backup_stats() -> dict:
    """Get backup system statistics."""
    try:
        backup_files = list(BACKUP_DIR.glob("full_backup_*.json"))
        latest_backup = None
        
        if backup_files:
            latest_backup = max(backup_files, key=os.path.getctime)
        
        return {
            "total_backups": len(backup_files),
            "max_backups": MAX_BACKUPS,
            "latest_backup": latest_backup.name if latest_backup else None,
            "cleanup_needed": len(backup_files) > MAX_BACKUPS
        }
    except Exception as e:
        logger.error(f"Failed to get backup stats: {e}")
        return {"error": str(e)}
