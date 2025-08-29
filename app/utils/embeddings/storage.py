"""
Storage utilities for embeddings.
"""

import sqlite3
import struct
from typing import List

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
