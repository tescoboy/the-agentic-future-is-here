"""
RAG database migrations and startup checks.
Copied from reference/signals-agent at commit ce1081c
Repository: https://github.com/adcontextprotocol/signals-agent

Ensures FTS5 and embeddings tables exist and are properly configured.
"""

import logging
from sqlalchemy.orm import Session
from app.models import Product
from app.utils.fts import create_products_fts_table, check_fts5_available
from app.utils.embeddings import generate_product_embedding, upsert_product_embeddings

logger = logging.getLogger(__name__)


def ensure_products_fts_exists(session: Session) -> None:
    """
    Ensure products FTS5 table exists.
    
    Args:
        session: Database session
        
    Raises:
        RuntimeError: If FTS5 is not available or table creation fails
    """
    try:
        # Check if FTS5 is available
        if not check_fts5_available(session):
            raise RuntimeError(
                "FTS5 is not available in SQLite. "
                "Please use a SQLite build with FTS5 enabled. "
                "On many systems, this requires installing sqlite3 with FTS5 support."
            )
        
        # Create FTS table
        create_products_fts_table(session)
        logger.info("Products FTS5 table created/verified successfully")
        
    except Exception as e:
        error_msg = f"Failed to create products FTS table: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def ensure_embeddings_table_exists(session: Session) -> None:
    """
    Ensure embeddings table exists.
    
    Args:
        session: Database session
        
    Raises:
        RuntimeError: If table creation fails
    """
    try:
        conn = session.connection().connection
        
        # Check if embeddings table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_embeddings'")
        
        if not cursor.fetchone():
            # Create embeddings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER UNIQUE NOT NULL,
                    embedding_text TEXT NOT NULL,
                    embedding_hash TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES product(id)
                )
            ''')
            
            # Create index
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_product_embeddings_product_id 
                ON product_embeddings(product_id)
            ''')
            
            conn.commit()
            logger.info("Product embeddings table created successfully")
        else:
            logger.info("Product embeddings table already exists")
            
    except Exception as e:
        error_msg = f"Failed to create embeddings table: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def ensure_vector_table_exists(session: Session) -> None:
    """
    Ensure vector similarity table exists.
    
    Args:
        session: Database session
        
    Raises:
        RuntimeError: If table creation fails
    """
    try:
        # Note: vec0 virtual table creation removed - using basic cosine similarity instead
        logger.info("Vector table creation skipped - using basic cosine similarity")
            
    except Exception as e:
        error_msg = f"Failed to create vector table: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


async def migrate_existing_products_to_rag(session: Session) -> None:
    """
    Migrate existing products to RAG by generating embeddings.
    
    Args:
        session: Database session
    """
    try:
        # Get all products without embeddings
        products = session.query(Product).all()
        
        if not products:
            logger.info("No products found for RAG migration")
            return
        
        logger.info(f"Starting RAG migration for {len(products)} products")
        
        migrated_count = 0
        for product in products:
            try:
                # Generate embedding for product
                embedding = await generate_product_embedding(product)
                if embedding:
                    # Store embedding
                    await upsert_product_embeddings(session, product.id, embedding)
                    migrated_count += 1
                    
                    if migrated_count % 10 == 0:
                        logger.info(f"Migrated {migrated_count}/{len(products)} products")
                        
            except Exception as e:
                logger.warning(f"Failed to migrate product {product.id}: {e}")
                continue
        
        logger.info(f"RAG migration completed: {migrated_count}/{len(products)} products migrated")
        
    except Exception as e:
        error_msg = f"Failed to migrate products to RAG: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def run_rag_startup_checks(session: Session) -> None:
    """
    Run all RAG startup checks and migrations.
    
    Args:
        session: Database session
        
    Raises:
        RuntimeError: If any check fails
    """
    try:
        logger.info("Starting RAG startup checks...")
        
        # Ensure FTS table exists
        ensure_products_fts_exists(session)
        
        # Ensure embeddings table exists
        ensure_embeddings_table_exists(session)
        
        # Ensure vector table exists
        ensure_vector_table_exists(session)
        
        logger.info("RAG startup checks completed successfully")
        
    except Exception as e:
        error_msg = f"RAG startup checks failed: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


async def run_rag_migrations(session: Session) -> None:
    """
    Run all RAG migrations including product embedding generation.
    
    Args:
        session: Database session
        
    Raises:
        RuntimeError: If any migration fails
    """
    try:
        logger.info("Starting RAG migrations...")
        
        # Run startup checks
        run_rag_startup_checks(session)
        
        # Migrate existing products
        await migrate_existing_products_to_rag(session)
        
        logger.info("RAG migrations completed successfully")
        
    except Exception as e:
        error_msg = f"RAG migrations failed: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
