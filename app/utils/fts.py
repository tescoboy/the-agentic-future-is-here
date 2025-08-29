"""
Full-text search (FTS5) utilities for product search.
Copied from reference/signals-agent at commit ce1081c
Repository: https://github.com/adcontextprotocol/signals-agent

Provides FTS5 virtual table creation and search functionality for products.
"""

import sqlite3
import re
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Product


def create_products_fts_table(session: Session) -> None:
    """
    Create FTS5 virtual table for products.
    Copied from signals-agent/adapters/liveramp.py _init_fts_table()
    
    Args:
        session: Database session
    """
    conn = session.connection().connection
    
    # Check if product table exists first (note: table is named 'product', not 'products')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
    if not cursor.fetchone():
        raise RuntimeError("Product table does not exist. Cannot create FTS table.")
    
    # Create FTS5 virtual table for products
    conn.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS products_fts 
        USING fts5(
            product_id UNINDEXED,
            name,
            description,
            content='product',
            content_rowid='id'
        )
    ''')
    
    # Create triggers to keep FTS table in sync
    conn.execute('''
        CREATE TRIGGER IF NOT EXISTS products_fts_insert 
        AFTER INSERT ON product BEGIN
            INSERT INTO products_fts(rowid, product_id, name, description)
            VALUES (new.id, new.id, new.name, new.description);
        END
    ''')
    
    conn.execute('''
        CREATE TRIGGER IF NOT EXISTS products_fts_delete 
        AFTER DELETE ON product BEGIN
            INSERT INTO products_fts(products_fts, rowid, product_id, name, description)
            VALUES('delete', old.id, old.id, old.name, old.description);
        END
    ''')
    
    conn.execute('''
        CREATE TRIGGER IF NOT EXISTS products_fts_update 
        AFTER UPDATE ON product BEGIN
            INSERT INTO products_fts(products_fts, rowid, product_id, name, description)
            VALUES('delete', old.id, old.id, old.name, old.description);
            INSERT INTO products_fts(rowid, product_id, name, description)
            VALUES (new.id, new.id, new.name, new.description);
        END
    ''')
    
    conn.commit()


def sync_products_to_fts(session: Session, products: List[Product]) -> None:
    """
    Sync products to FTS table.
    
    Args:
        session: Database session
        products: List of products to sync
    """
    conn = session.connection().connection
    
    # Ensure FTS table exists
    create_products_fts_table(session)
    
    # Clear existing data for these products
    if products:
        product_ids = [p.id for p in products]
        placeholders = ','.join('?' * len(product_ids))
        conn.execute(f'''
            DELETE FROM products_fts 
            WHERE product_id IN ({placeholders})
        ''', product_ids)
    
    # Insert products into FTS table
    for product in products:
        conn.execute('''
            INSERT INTO products_fts(product_id, name, description)
            VALUES (?, ?, ?)
        ''', (product.id, product.name, product.description))
    
    conn.commit()


def fts_search_products(session: Session, tenant_id: int, query: str, limit: int) -> List[Dict[str, Any]]:
    """
    Search products using FTS5.
    Copied from signals-agent/adapters/liveramp.py search_segments()
    
    Args:
        session: Database session
        tenant_id: Tenant ID to filter products
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of product dicts with relevance scores
    """
    # Properly sanitize query to prevent SQL injection
    # Only allow alphanumeric, spaces, and basic punctuation
    sanitized_query = re.sub(r'[^\w\s\-]', ' ', query)
    words = sanitized_query.lower().split()
    
    # Build FTS query terms
    fts_terms = []
    for word in words:
        if len(word) >= 2:  # Skip very short words
            fts_terms.append(f'"{word}"')
    
    if not fts_terms:
        # No valid search terms, return empty results
        return []
    
    fts_query = ' OR '.join(fts_terms)
    
    try:
        conn = session.connection().connection
        
        # Ensure FTS table exists
        create_products_fts_table(session)
        
        # Search using FTS5
        cursor = conn.execute('''
            SELECT p.id, p.name, p.description, p.price_cpm, p.delivery_type,
                   p.formats_json, p.targeting_json,
                   1.0 as relevance_score
            FROM product p
            JOIN products_fts fts ON p.id = fts.rowid
            WHERE p.tenant_id = ? AND products_fts MATCH ?
            LIMIT ?
        ''', (tenant_id, fts_query, limit))
        
        results = []
        for row in cursor.fetchall():
            result = {
                'product_id': row[0],
                'name': row[1],
                'description': row[2],
                'price_cpm': row[3],
                'delivery_type': row[4],
                'formats_json': row[5],
                'targeting_json': row[6],
                'relevance_score': row[7] or 1.0  # FTS results have maximum relevance
            }
            results.append(result)
        
        return results
        
    except Exception as e:
        # Fall back to simple text search if FTS fails
        return _fallback_text_search(session, tenant_id, query, limit)


def _fallback_text_search(session: Session, tenant_id: int, query: str, limit: int) -> List[Dict[str, Any]]:
    """
    Fallback text search when FTS is not available.
    
    Args:
        session: Database session
        tenant_id: Tenant ID to filter products
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of product dicts with relevance scores
    """
    # Simple LIKE-based search as fallback
    search_terms = query.lower().split()
    
    products = session.query(Product).filter(Product.tenant_id == tenant_id).all()
    
    results = []
    for product in products:
        # Calculate simple relevance score based on term matches
        product_text = f"{product.name} {product.description}".lower()
        matches = sum(1 for term in search_terms if term in product_text)
        
        if matches > 0:
            relevance_score = matches / len(search_terms) if search_terms else 0
            
            result = {
                'product_id': product.id,
                'name': product.name,
                'description': product.description,
                'price_cpm': product.price_cpm,
                'delivery_type': product.delivery_type,
                'formats_json': product.formats_json,
                'targeting_json': product.targeting_json,
                'relevance_score': relevance_score
            }
            results.append(result)
    
    # Sort by relevance score
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    return results[:limit]


def check_fts5_available(session: Session) -> bool:
    """
    Check if FTS5 is available in SQLite.
    
    Args:
        session: Database session
        
    Returns:
        True if FTS5 is available, False otherwise
    """
    try:
        conn = session.connection().connection
        
        # Check SQLite version
        cursor = conn.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]
        
        # Check FTS5 compile options
        cursor = conn.execute("PRAGMA compile_options")
        compile_options = [row[0] for row in cursor.fetchall()]
        
        return 'ENABLE_FTS5' in compile_options
        
    except Exception:
        return False
