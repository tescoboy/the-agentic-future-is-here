"""
Embeddings backfill service for processing existing products.
Handles batch embedding of products missing vectors.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.utils.embeddings_config import get_embeddings_config
from app.utils.embeddings import batch_embed_text, upsert_product_embeddings
from app.models import Product

logger = logging.getLogger(__name__)


def find_products_needing_embeddings(session: Session, limit: int = 1000, last_seen_id: int = 0) -> List[int]:
    """
    Find products that need embeddings using pagination.
    
    Args:
        session: Database session
        limit: Maximum number of products to return
        last_seen_id: Last product ID seen (for pagination)
        
    Returns:
        List of product IDs needing embeddings
    """
    config = get_embeddings_config()
    
    # Use pagination to avoid large OFFSET scans
    query = text('''
        SELECT p.id 
        FROM product p
        LEFT JOIN product_embeddings pe ON p.id = pe.product_id 
            AND pe.provider = :provider 
            AND pe.model = :model 
            AND pe.is_stale = 0
        WHERE p.id > :last_seen_id 
            AND pe.id IS NULL
        ORDER BY p.id
        LIMIT :limit
    ''')
    
    result = session.execute(query, {
        'provider': config['provider'],
        'model': config['model'],
        'last_seen_id': last_seen_id,
        'limit': limit
    })
    
    return [row[0] for row in result.fetchall()]


async def backfill_once(session: Session, batch_size: int = 32) -> Dict[str, Any]:
    """
    Process one batch of products needing embeddings.
    
    Args:
        session: Database session
        batch_size: Number of products to process in this batch
        
    Returns:
        Dictionary with processing results
    """
    config = get_embeddings_config()
    
    # Find products needing embeddings
    product_ids = find_products_needing_embeddings(session, limit=batch_size)
    
    if not product_ids:
        return {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'remaining': 0,
            'last_seen_id': 0
        }
    
    logger.info(f"Backfilling embeddings for {len(product_ids)} products")
    
    try:
        # Get product texts for embedding
        products = session.query(Product).filter(Product.id.in_(product_ids)).all()
        product_texts = {p.id: f"{p.name}\n{p.description}" for p in products}
        
        if not product_texts:
            return {
                'processed': len(product_ids),
                'successful': 0,
                'failed': len(product_ids),
                'remaining': 0,
                'last_seen_id': max(product_ids) if product_ids else 0
            }
        
        # Generate embeddings
        texts = list(product_texts.values())
        embeddings = await batch_embed_text(texts)
        
        if not embeddings or len(embeddings) != len(texts):
            logger.error(f"Embedding generation failed: expected {len(texts)}, got {len(embeddings) if embeddings else 0}")
            return {
                'processed': len(product_ids),
                'successful': 0,
                'failed': len(product_ids),
                'remaining': 0,
                'last_seen_id': max(product_ids) if product_ids else 0
            }
        
        # Store embeddings
        successful = 0
        failed = 0
        
        for i, product_id in enumerate(product_ids):
            try:
                if i < len(embeddings):
                    embedding = embeddings[i]
                    embedding_text = product_texts[product_id]
                    
                    # Create embedding hash
                    import hashlib
                    hash_input = f"{embedding_text}:{config['provider']}:{config['model']}:{len(embedding)}"
                    embedding_hash = hashlib.sha256(hash_input.encode()).hexdigest()
                    
                    # Store embedding
                    await upsert_product_embeddings(
                        session, product_id, embedding,
                        provider=config['provider'],
                        model=config['model'],
                        dim=len(embedding),
                        embedding_hash=embedding_hash
                    )
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Failed to store embedding for product {product_id}: {e}")
                failed += 1
        
        # Check how many more products need embeddings
        remaining = len(find_products_needing_embeddings(session, limit=1))
        
        logger.info(f"Backfill batch completed: {successful} successful, {failed} failed, {remaining} remaining")
        
        return {
            'processed': len(product_ids),
            'successful': successful,
            'failed': failed,
            'remaining': remaining,
            'last_seen_id': max(product_ids) if product_ids else 0
        }
        
    except Exception as e:
        logger.error(f"Backfill batch failed: {e}")
        return {
            'processed': len(product_ids),
            'successful': 0,
            'failed': len(product_ids),
            'remaining': 0,
            'last_seen_id': max(product_ids) if product_ids else 0
        }


def mark_stale_vectors(session: Session, provider: str, model: str) -> int:
    """
    Mark existing vectors as stale when provider or model changes.
    
    Args:
        session: Database session
        provider: New provider
        model: New model
        
    Returns:
        Number of vectors marked as stale
    """
    query = text('''
        UPDATE product_embeddings 
        SET is_stale = 1 
        WHERE provider = :provider AND model = :model AND is_stale = 0
    ''')
    
    result = session.execute(query, {
        'provider': provider,
        'model': model
    })
    
    session.commit()
    
    # Get count of affected rows
    count_query = text('''
        SELECT COUNT(*) FROM product_embeddings 
        WHERE provider = :provider AND model = :model AND is_stale = 1
    ''')
    
    count_result = session.execute(count_query, {
        'provider': provider,
        'model': model
    })
    
    count = count_result.scalar()
    logger.info(f"Marked {count} vectors as stale for provider={provider}, model={model}")
    
    return count


def get_vector_counts(session: Session) -> Dict[str, int]:
    """
    Get vector counts for monitoring.
    
    Args:
        session: Database session
        
    Returns:
        Dictionary with vector counts
    """
    config = get_embeddings_config()
    
    # Count current model vectors
    current_query = text('''
        SELECT COUNT(*) FROM product_embeddings 
        WHERE provider = :provider AND model = :model AND is_stale = 0
    ''')
    
    current_result = session.execute(current_query, {
        'provider': config['provider'],
        'model': config['model']
    })
    
    current_count = current_result.scalar()
    
    # Count all vectors
    all_query = text('SELECT COUNT(*) FROM product_embeddings')
    all_result = session.execute(all_query)
    all_count = all_result.scalar()
    
    return {
        'vector_count_current_model': current_count,
        'vector_count_all': all_count
    }
