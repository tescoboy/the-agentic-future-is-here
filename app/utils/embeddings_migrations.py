"""
Database migrations for embeddings system.
Adds metadata columns and indexes to product_embeddings table.
"""

import logging
from sqlalchemy.orm import Session
from datetime import datetime

logger = logging.getLogger(__name__)


def run_embeddings_migrations(session: Session) -> None:
    """
    Run all embeddings-related database migrations.
    
    Args:
        session: Database session
    """
    logger.info("Starting embeddings migrations...")
    
    # Add new columns to product_embeddings table
    _add_embeddings_metadata_columns(session)
    
    # Create indexes for performance
    _create_embeddings_indexes(session)
    
    # Migrate existing data
    _migrate_existing_embeddings(session)
    
    logger.info("Embeddings migrations completed successfully")


def _add_embeddings_metadata_columns(session: Session) -> None:
    """Add metadata columns to product_embeddings table."""
    conn = session.connection().connection
    
    # Check if columns already exist
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(product_embeddings)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Add new columns if they don't exist
    new_columns = [
        ('provider', 'TEXT'),
        ('model', 'TEXT'),
        ('dim', 'INTEGER'),
        ('updated_at', 'TEXT'),
        ('is_stale', 'INTEGER DEFAULT 0')
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            logger.info(f"Adding column {col_name} to product_embeddings")
            conn.execute(f'ALTER TABLE product_embeddings ADD COLUMN {col_name} {col_type}')


def _create_embeddings_indexes(session: Session) -> None:
    """Create indexes for embeddings performance."""
    conn = session.connection().connection
    cursor = conn.cursor()
    
    # Check existing indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='product_embeddings'")
    existing_indexes = [row[0] for row in cursor.fetchall()]
    
    # Create unique index for versioning (product_id, provider, model)
    if 'idx_product_embeddings_version' not in existing_indexes:
        logger.info("Creating unique index for embedding versioning")
        conn.execute('''
            CREATE UNIQUE INDEX idx_product_embeddings_version 
            ON product_embeddings(product_id, provider, model)
        ''')
    
    # Create performance index for current vectors
    if 'idx_product_embeddings_current' not in existing_indexes:
        logger.info("Creating performance index for current embeddings")
        conn.execute('''
            CREATE INDEX idx_product_embeddings_current 
            ON product_embeddings(provider, model, is_stale) 
            WHERE is_stale = 0
        ''')


def _migrate_existing_embeddings(session: Session) -> None:
    """Migrate existing embeddings to new schema."""
    conn = session.connection().connection
    cursor = conn.cursor()
    
    # Check if we have existing embeddings to migrate
    cursor.execute("SELECT COUNT(*) FROM product_embeddings WHERE provider IS NULL")
    count = cursor.fetchone()[0]
    
    if count > 0:
        logger.info(f"Migrating {count} existing embeddings to new schema")
        
        # Update existing embeddings with default values
        now = datetime.utcnow().isoformat()
        cursor.execute('''
            UPDATE product_embeddings 
            SET provider = 'gemini', 
                model = 'text-embedding-004', 
                dim = 768,
                updated_at = ?,
                is_stale = 0
            WHERE provider IS NULL
        ''', (now,))
        
        logger.info(f"Migrated {count} embeddings successfully")
    else:
        logger.info("No existing embeddings to migrate")
