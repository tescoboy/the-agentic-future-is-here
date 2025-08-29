"""
CSV import functions for seed data.
"""

import csv
import json
import logging
import os
from pathlib import Path
from sqlalchemy.orm import Session

from app.models import Tenant, Product
from app.repos.tenants import create_tenant
from app.repos.products import create_product

logger = logging.getLogger(__name__)


def _seed_from_csv(session: Session) -> bool:
    """Seed tenants and products from CSV file. Returns True if successful, False otherwise."""
    # Try multiple possible paths
    possible_paths = [
        "./catalog_final.csv",
        "catalog_final.csv",
        "../catalog_final.csv",
        Path(__file__).parent.parent.parent / "catalog_final.csv"
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        logger.warning(f"CSV file not found in any of these locations: {possible_paths}")
        return False
    
    logger.info(f"Found CSV file at: {csv_path}")
    
    # Track created tenants
    tenants = {}
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        product_count = 0
        for row in reader:
            tenant_slug = row['tenant_slug']
            
            # Skip rows with empty tenant slugs
            if not tenant_slug or not tenant_slug.strip():
                logger.warning(f"Skipping row with empty tenant_slug: {row.get('product_name', 'Unknown')}")
                continue
            
            # Create tenant if it doesn't exist
            if tenant_slug not in tenants:
                try:
                    tenant = _ensure_tenant_from_csv(session, tenant_slug)
                    tenants[tenant_slug] = tenant
                except ValueError as e:
                    logger.warning(f"Skipping row due to tenant validation error: {e}")
                    continue
            
            # Create product
            _create_product_from_csv(session, row, tenants[tenant_slug].id)
            product_count += 1
            
            # Log progress every 100 products
            if product_count % 100 == 0:
                logger.info(f"Processed {product_count} products...")
    
    logger.info(f"Seeded {len(tenants)} tenants with {product_count} products from CSV")
    return True


def _ensure_tenant_from_csv(session: Session, tenant_slug: str) -> Tenant:
    """Ensure tenant exists, create if it doesn't."""
    # Validate tenant_slug is not empty
    if not tenant_slug or not tenant_slug.strip():
        raise ValueError("Tenant name cannot be empty")
    
    existing_tenant = session.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    if existing_tenant:
        logger.info(f"Tenant already exists: {existing_tenant.name}")
        return existing_tenant
    
    # Create tenant with appropriate name
    tenant_names = {
        'tiktok': 'TikTok',
        'iheart-radio': 'iHeart Radio',
        'netflix': 'Netflix',
        'nytimes': 'New York Times'
    }
    
    tenant_name = tenant_names.get(tenant_slug, tenant_slug.title())
    tenant = create_tenant(session, tenant_name, tenant_slug)
    logger.info(f"Created tenant: {tenant.name}")
    return tenant


def _create_product_from_csv(session: Session, row: dict, tenant_id: int) -> None:
    """Create product from CSV row."""
    # Check if product already exists
    existing_product = session.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.name == row['product_name']
    ).first()
    
    if existing_product:
        return  # Product already exists
    
    # Create product
    product = create_product(
        session=session,
        tenant_id=tenant_id,
        name=row['product_name'],
        description=row['description'],
        price_cpm=float(row['price_cpm']),
        delivery_type=row['delivery_type'],
        formats_json=row['formats'],
        targeting_json=row['targeting_json']
    )
    
    logger.debug(f"Created product: {product.name}")
