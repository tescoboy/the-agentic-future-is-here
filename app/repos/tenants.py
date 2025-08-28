"""
Tenant repository operations.
"""

from typing import List, Optional
from sqlmodel import Session, select
from app.models import Tenant


def create_tenant(session: Session, name: str, slug: str) -> Tenant:
    """Create a new tenant."""
    tenant = Tenant(name=name, slug=slug)
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


def get_tenant_by_id(session: Session, tenant_id: int) -> Optional[Tenant]:
    """Get tenant by ID."""
    return session.get(Tenant, tenant_id)


def get_tenant_by_slug(session: Session, slug: str) -> Optional[Tenant]:
    """Get tenant by slug."""
    statement = select(Tenant).where(Tenant.slug == slug)
    return session.exec(statement).first()


def list_tenants(session: Session, q: str = "", limit: int = 20, offset: int = 0) -> tuple[List[Tenant], int]:
    """List tenants with search and pagination."""
    statement = select(Tenant)
    
    if q:
        statement = statement.where(
            Tenant.name.contains(q) | Tenant.slug.contains(q)
        )
    
    # Get total count
    count_statement = select(Tenant)
    if q:
        count_statement = count_statement.where(
            Tenant.name.contains(q) | Tenant.slug.contains(q)
        )
    total = len(session.exec(count_statement).all())
    
    # Get paginated results
    statement = statement.offset(offset).limit(limit)
    tenants = session.exec(statement).all()
    
    return tenants, total


def update_tenant(session: Session, tenant_id: int, name: str, slug: str) -> Optional[Tenant]:
    """Update a tenant."""
    tenant = get_tenant_by_id(session, tenant_id)
    if not tenant:
        return None
    
    tenant.name = name
    tenant.slug = slug
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


def delete_tenant(session: Session, tenant_id: int) -> bool:
    """Delete a tenant."""
    tenant = get_tenant_by_id(session, tenant_id)
    if not tenant:
        return False
    
    session.delete(tenant)
    session.commit()
    return True


def bulk_delete_all_tenants(session: Session) -> int:
    """Delete all tenants and return the count of deleted tenants."""
    from app.models import Product
    
    # First, delete all products (they reference tenants)
    product_statement = select(Product)
    products = session.exec(product_statement).all()
    for product in products:
        session.delete(product)
    
    # Then delete all tenants
    statement = select(Tenant)
    tenants = session.exec(statement).all()
    
    deleted_count = len(tenants)
    for tenant in tenants:
        session.delete(tenant)
    
    session.commit()
    return deleted_count

