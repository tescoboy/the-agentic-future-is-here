#!/usr/bin/env python3
"""
Convenience script for creating full optimized backups.
Can be used for automated backups, scheduled tasks, etc.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, ensure_database
from app.utils.data_persistence.optimized_backup import create_optimized_backup

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """Create a full optimized backup."""
    try:
        logger.info("🚀 Starting full optimized backup...")
        
        # Ensure database exists
        ensure_database()
        
        # Get database session
        session = next(get_session())
        
        try:
            # Create the backup
            result = await create_optimized_backup(session, use_compression=True)
            logger.info(f"✅ {result}")
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
