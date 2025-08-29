"""
Query and search functions for embeddings.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models import Product
from .storage import _bytes_to_embedding


async def search_similar_products(session: Session, tenant_id: int, query_embedding: List[float], limit: int) -> List[Dict[str, Any]]:
    """
    Find products with similar embeddings using cosine similarity.
    
    Args:
        session: Database session
        tenant_id: Tenant ID to filter products
        query_embedding: Query embedding vector
        limit: Maximum number of results
        
    Returns:
        List of product dicts with similarity scores
    """
    try:
        # Get current embedding configuration
        from app.utils.embeddings_config import get_embeddings_config
        config = get_embeddings_config()
        
        # Use raw SQL to get all embeddings for the tenant
        conn = session.connection().connection
        cursor = conn.cursor()
        
        # Get all products with current embeddings for this tenant
        cursor.execute('''
            SELECT p.id, p.name, p.description, p.price_cpm, p.delivery_type,
                   p.formats_json, p.targeting_json, pe.embedding
            FROM product_embeddings pe
            JOIN product p ON pe.product_id = p.id
            WHERE p.tenant_id = ? 
            AND pe.provider = ? 
            AND pe.model = ? 
            AND pe.is_stale = 0
        ''', (tenant_id, config['provider'], config['model']))
        
        results = []
        for row in cursor.fetchall():
            product_id, name, description, price_cpm, delivery_type, formats_json, targeting_json, embedding_bytes = row
            
            # Convert embedding bytes back to list
            embedding_array = _bytes_to_embedding(embedding_bytes)
            embedding_list = embedding_array
            
            # Calculate cosine similarity
            similarity = _cosine_similarity(query_embedding, embedding_list)
            
            result = {
                'product_id': product_id,
                'name': name,
                'description': description,
                'price_cpm': price_cpm,
                'delivery_type': delivery_type,
                'formats_json': formats_json,
                'targeting_json': targeting_json,
                'similarity_score': similarity
            }
            results.append(result)
        
        # Sort by similarity score (descending) and limit results
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:limit]
        
    except Exception as e:
        # Fall back to simple text search if vector search fails
        return await _fallback_text_search(session, tenant_id, limit)


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    try:
        # Convert to numpy arrays
        a = vec1
        b = vec2
        
        # Calculate cosine similarity
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x**2 for x in a)**0.5
        norm_b = sum(x**2 for x in b)**0.5
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    except Exception:
        return 0.0


async def _fallback_text_search(session: Session, tenant_id: int, limit: int) -> List[Dict[str, Any]]:
    """
    Fallback text search when vector search is not available.
    
    Args:
        session: Database session
        tenant_id: Tenant ID to filter products
        limit: Maximum number of results
        
    Returns:
        List of product dicts with similarity scores
    """
    products = session.query(Product).filter(Product.tenant_id == tenant_id).limit(limit).all()
    
    results = []
    for product in products:
        result = {
            'product_id': product.id,
            'name': product.name,
            'description': product.description,
            'price_cpm': product.price_cpm,
            'delivery_type': product.delivery_type,
            'formats_json': product.formats_json,
            'targeting_json': product.targeting_json,
            'similarity_score': 0.5  # Default fallback score
        }
        results.append(result)
    
    return results


def get_product_embeddings(session: Session, product_id: int) -> List[Dict[str, Any]]:
    """
    Get all embeddings for a specific product.
    
    Args:
        session: Database session
        product_id: Product ID
        
    Returns:
        List of embedding metadata
    """
    conn = session.connection().connection
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT provider, model, dim, updated_at, is_stale, embedding_hash
        FROM product_embeddings
        WHERE product_id = ?
        ORDER BY updated_at DESC
    ''', (product_id,))
    
    results = []
    for row in cursor.fetchall():
        provider, model, dim, updated_at, is_stale, embedding_hash = row
        results.append({
            'provider': provider,
            'model': model,
            'dim': dim,
            'updated_at': updated_at,
            'is_stale': bool(is_stale),
            'embedding_hash': embedding_hash
        })
    
    return results
