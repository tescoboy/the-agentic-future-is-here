"""
Embedding generation functions.
"""

import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models import Product
from app.utils.env import get_gemini_api_key
from .storage import _embedding_to_bytes, _ensure_embeddings_table_schema

# Constants copied from signals-agent
EMBEDDING_DIMENSION = 768  # text-embedding-004 produces 768-dim vectors


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
        hash_input = f"{embedding_text}:{provider}:{model}:{dim}"
        embedding_hash = hashlib.sha256(hash_input.encode()).hexdigest()
    
    # Set defaults if not provided
    if not updated_at:
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
