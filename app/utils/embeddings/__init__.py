"""
Vector embeddings management for RAG implementation using Gemini.
Copied from reference/signals-agent at commit ce1081c
Repository: https://github.com/adcontextprotocol/signals-agent

Provides vector embedding generation and similarity search for products.
"""

from .generator import batch_embed_text, upsert_product_embeddings, generate_product_embedding
from .storage import _ensure_embeddings_table_schema, _embedding_to_bytes, _bytes_to_embedding
from .query import search_similar_products, get_product_embeddings

__all__ = [
    'batch_embed_text',
    'upsert_product_embeddings', 
    'generate_product_embedding',
    '_ensure_embeddings_table_schema',
    '_embedding_to_bytes',
    '_bytes_to_embedding',
    'search_similar_products',
    'get_product_embeddings'
]
