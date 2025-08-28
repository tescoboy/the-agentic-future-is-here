"""
Product repository operations.
"""

from typing import List, Optional
from sqlmodel import Session, select
from app.models import Product


def create_product(session: Session, tenant_id: int, name: str, description: str, 
                  price_cpm: float, delivery_type: str, formats_json: str = "{}", 
                  targeting_json: str = "{}") -> Product:
    """Create a new product."""
    product = Product(
        tenant_id=tenant_id,
        name=name,
        description=description,
        price_cpm=price_cpm,
        delivery_type=delivery_type,
        formats_json=formats_json,
        targeting_json=targeting_json
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def get_product_by_id(session: Session, product_id: int) -> Optional[Product]:
    """Get product by ID."""
    return session.get(Product, product_id)


def list_products(session: Session, tenant_id: Optional[int] = None, q: str = "", 
                 sort: str = "created_at", order: str = "desc", 
                 limit: int = 20, offset: int = 0) -> tuple[List[Product], int]:
    """List products with search, sort, and pagination."""
    statement = select(Product)
    
    # Filter by tenant if specified
    if tenant_id:
        statement = statement.where(Product.tenant_id == tenant_id)
    
    # Search across name and description
    if q:
        statement = statement.where(
            Product.name.contains(q) | Product.description.contains(q)
        )
    
    # Validate sort field
    valid_sort_fields = {"name", "price_cpm", "created_at"}
    if sort not in valid_sort_fields:
        sort = "created_at"
    
    # Apply sorting
    if order.lower() == "asc":
        statement = statement.order_by(getattr(Product, sort))
    else:
        statement = statement.order_by(getattr(Product, sort).desc())
    
    # Get total count
    count_statement = select(Product)
    if tenant_id:
        count_statement = count_statement.where(Product.tenant_id == tenant_id)
    if q:
        count_statement = count_statement.where(
            Product.name.contains(q) | Product.description.contains(q)
        )
    total = len(session.exec(count_statement).all())
    
    # Get paginated results
    statement = statement.offset(offset).limit(limit)
    products = session.exec(statement).all()
    
    return products, total


def update_product(session: Session, product_id: int, tenant_id: int, name: str, 
                  description: str, price_cpm: float, delivery_type: str, 
                  formats_json: str = "{}", targeting_json: str = "{}") -> Optional[Product]:
    """Update a product."""
    product = get_product_by_id(session, product_id)
    if not product:
        return None
    
    product.tenant_id = tenant_id
    product.name = name
    product.description = description
    product.price_cpm = price_cpm
    product.delivery_type = delivery_type
    product.formats_json = formats_json
    product.targeting_json = targeting_json
    
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def delete_product(session: Session, product_id: int) -> bool:
    """Delete a product."""
    product = get_product_by_id(session, product_id)
    if not product:
        return False
    
    session.delete(product)
    session.commit()
    return True


def bulk_delete_products(session: Session, product_ids: List[int]) -> int:
    """Bulk delete products. Returns count of deleted products."""
    deleted_count = 0
    for product_id in product_ids:
        if delete_product(session, product_id):
            deleted_count += 1
    return deleted_count

