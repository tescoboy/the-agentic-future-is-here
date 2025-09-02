#!/usr/bin/env python3
"""
Convenience script for restoring from optimized backups.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, ensure_database
from app.utils.data_persistence.optimized_backup import restore_optimized_backup

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """Restore from the most recent optimized backup."""
    try:
        logger.info("🔄 Starting optimized backup restore...")
        
        # Ensure database exists
        ensure_database()
        
        # Get database session
        session = next(get_session())
        
        try:
            # Restore from most recent backup
            result = await restore_optimized_backup(session, backup_file=None, validate=True)
            logger.info(f"✅ {result}")
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"❌ Restore failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Confirm before proceeding
    response = input("⚠️ This will replace all existing data. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Restore cancelled")
        sys.exit(0)
    
    asyncio.run(main())
