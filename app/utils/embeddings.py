"""
Vector embeddings management for RAG implementation using Gemini.
Copied from reference/signals-agent at commit ce1081c
Repository: https://github.com/adcontextprotocol/signals-agent

Provides vector embedding generation and similarity search for products.
"""

import sqlite3
import json
import struct
from typing import List, Dict, Any, Optional
import asyncio
from sqlalchemy.orm import Session
from app.models import Product
from app.utils.env import get_gemini_api_key

# Constants copied from signals-agent
EMBEDDING_DIMENSION = 768  # text-embedding-004 produces 768-dim vectors


def _embedding_to_bytes(embedding: List[float]) -> bytes:
    """Convert embedding list to bytes using struct module instead of numpy."""
    return struct.pack(f'{len(embedding)}f', *embedding)


def _bytes_to_embedding(embedding_bytes: bytes) -> List[float]:
    """Convert bytes back to embedding list using struct module instead of numpy."""
    return list(struct.unpack(f'{len(embedding_bytes)//4}f', embedding_bytes))


def _ensure_embeddings_table_schema(conn) -> None:
    """Ensure the product_embeddings table has all required columns."""
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(product_embeddings)")
    columns = {row[1] for row in cursor.fetchall()}
    
    # Add missing columns
    missing_columns = [
        ('provider', 'TEXT'),
        ('model', 'TEXT'),
        ('dim', 'INTEGER'),
        ('updated_at', 'TEXT'),
        ('is_stale', 'INTEGER DEFAULT 0')
    ]
    
    for col_name, col_type in missing_columns:
        if col_name not in columns:
            try:
                conn.execute(f'ALTER TABLE product_embeddings ADD COLUMN {col_name} {col_type}')
                print(f"Added column {col_name} to product_embeddings table")
            except Exception as e:
                print(f"Column {col_name} might already exist: {e}")


async def batch_embed_text(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts using Gemini.
    Copied from signals-agent/embeddings.py generate_embedding()
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors (768-dimensional)
        
    Raises:
        ValueError: If Gemini API key is missing
    """
    try:
        import google.generativeai as genai
        
        api_key = get_gemini_api_key()
        if not api_key:
            raise ValueError("Gemini API key is required for embeddings")
        
        genai.configure(api_key=api_key)
        
        embeddings = []
        for text in texts:
            # Generate embedding using Gemini
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            
            # Extract embedding vector
            embedding = result['embedding']
            embeddings.append(embedding)
        
        return embeddings
        
    except Exception as e:
        raise ValueError(f"Failed to generate embeddings: {e}")


async def upsert_product_embeddings(session: Session, product_id: int, embedding: List[float], 
                                   provider: str = None, model: str = None, dim: int = None,
                                   updated_at: str = None, embedding_hash: str = None) -> None:
    """
    Store or update product embedding in the database with metadata.
    
    Args:
        session: Database session
        product_id: Product ID
        embedding: Embedding vector
        provider: Embedding provider (e.g., 'gemini')
        model: Embedding model (e.g., 'text-embedding-004')
        dim: Embedding dimension
        updated_at: ISO timestamp
        embedding_hash: Pre-computed hash
    """
    # Convert embedding to bytes for storage using struct instead of numpy
    embedding_bytes = _embedding_to_bytes(embedding)
    
    # Use raw SQL for embedding storage
    conn = session.connection().connection
    
    # Create embeddings table if it doesn't exist (with new columns)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS product_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            embedding_text TEXT NOT NULL,
            embedding_hash TEXT NOT NULL,
            embedding BLOB NOT NULL,
            provider TEXT,
            model TEXT,
            dim INTEGER,
            updated_at TEXT,
            is_stale INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES product(id)
        )
    ''')
    
    # Ensure all required columns exist (migrate existing tables)
    _ensure_embeddings_table_schema(conn)
    
    # Get product text for embedding
    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        return
    
    # Create embedding text (name + description)
    embedding_text = f"{product.name}\n{product.description}"
    
    # Use provided hash or create one
    if not embedding_hash:
        import hashlib
        hash_input = f"{embedding_text}:{provider}:{model}:{dim}"
        embedding_hash = hashlib.sha256(hash_input.encode()).hexdigest()
    
    # Set defaults if not provided
    if not updated_at:
        from datetime import datetime
        updated_at = datetime.utcnow().isoformat()
    
    # Check if embedding already exists for this provider/model
    cursor = conn.cursor()
    cursor.execute('''
        SELECT embedding_hash, is_stale FROM product_embeddings 
        WHERE product_id = ? AND provider = ? AND model = ?
    ''', (product_id, provider, model))
    existing = cursor.fetchone()
    
    if existing and existing[0] == embedding_hash and existing[1] == 0:
        # Embedding is up to date and not stale
        return
    
    # Mark any existing embeddings for this product/provider/model as stale
    cursor.execute('''
        UPDATE product_embeddings 
        SET is_stale = 1 
        WHERE product_id = ? AND provider = ? AND model = ?
    ''', (product_id, provider, model))
    
    # Insert new embedding
    cursor.execute('''
        INSERT INTO product_embeddings 
        (product_id, embedding_text, embedding_hash, embedding, provider, model, dim, updated_at, is_stale)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (product_id, embedding_text, embedding_hash, embedding_bytes, provider, model, dim, updated_at))
    
    conn.commit()


async def query_similar_embeddings(session: Session, tenant_id: int, query_embedding: List[float], limit: int) -> List[Dict[str, Any]]:
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


async def generate_product_embedding(product: Product) -> List[float]:
    """
    Generate embedding for a single product.
    
    Args:
        product: Product model instance
        
    Returns:
        Embedding vector (768-dimensional)
    """
    # Create embedding text (name + description)
    embedding_text = f"{product.name}\n{product.description}"
    
    # Generate embedding
    embeddings = await batch_embed_text([embedding_text])
    return embeddings[0] if embeddings else []
