"""
Database migration utilities.
"""

import logging
from sqlalchemy import text
from app.db import get_engine

logger = logging.getLogger(__name__)


def run_migrations():
    """Run database migrations safely."""
    engine = get_engine()
    
    try:
        with engine.connect() as conn:
            # Check if externalagent table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='externalagent'"))
            if not result.fetchone():
                logger.info("externalagent table does not exist, skipping migrations")
                return
            
            # Get existing columns
            result = conn.execute(text("PRAGMA table_info(externalagent)"))
            columns = {row[1] for row in result.fetchall()}
            
            # Add agent_type column if missing
            if "agent_type" not in columns:
                sql = "ALTER TABLE externalagent ADD COLUMN agent_type TEXT DEFAULT 'sales'"
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("Added agent_type column to externalagent table")
                except Exception as e:
                    raise RuntimeError(f"Migration failed for table externalagent. SQL: {sql}. Error: {str(e)}")
            
            # Add protocol column if missing
            if "protocol" not in columns:
                sql = "ALTER TABLE externalagent ADD COLUMN protocol TEXT DEFAULT 'rest'"
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("Added protocol column to externalagent table")
                except Exception as e:
                    raise RuntimeError(f"Migration failed for table externalagent. SQL: {sql}. Error: {str(e)}")
            
            logger.info("DB migrations complete: external_agents validated")
            
        # Migrate tenants table for custom_prompt
        with engine.connect() as conn:
            # Check if tenant table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='tenant'"))
            if not result.fetchone():
                logger.info("tenant table does not exist, skipping custom_prompt migration")
                return
            
            # Get existing columns
            result = conn.execute(text("PRAGMA table_info(tenant)"))
            columns = {row[1] for row in result.fetchall()}
            
            # Add custom_prompt column if missing
            if "custom_prompt" not in columns:
                sql = "ALTER TABLE tenant ADD COLUMN custom_prompt TEXT"
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("Added custom_prompt column to tenant table")
                except Exception as e:
                    raise RuntimeError(f"Migration failed for table tenant. SQL: {sql}. Error: {str(e)}")
            
            # Add web_grounding_prompt column if missing
            if "web_grounding_prompt" not in columns:
                sql = "ALTER TABLE tenant ADD COLUMN web_grounding_prompt TEXT"
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("Added web_grounding_prompt column to tenant table")
                except Exception as e:
                    raise RuntimeError(f"Migration failed for table tenant. SQL: {sql}. Error: {str(e)}")
            
            # Add enable_web_context column if missing
            if "enable_web_context" not in columns:
                sql = "ALTER TABLE tenant ADD COLUMN enable_web_context BOOLEAN DEFAULT 0"
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("Added enable_web_context column to tenant table")
                except Exception as e:
                    raise RuntimeError(f"Migration failed for table tenant. SQL: {sql}. Error: {str(e)}")
            
            logger.info("DB migrations complete: tenant custom_prompt validated")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

