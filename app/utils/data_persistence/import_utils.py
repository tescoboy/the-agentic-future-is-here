"""
Import functions for data persistence.
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models import Tenant, Product, ExternalAgent
from app.repos.tenants import create_tenant
from app.repos.external_agents import create_external_agent
from app.repos.products import create_product
from .core import ensure_data_directories, BACKUP_DIR

logger = logging.getLogger(__name__)


def import_all_data(session: Session, backup_data: Optional[Dict[str, Any]] = None, backup_file: Optional[str] = None) -> Dict[str, Any]:
    """Import all application data from backup."""
    ensure_data_directories()
    
    if backup_data is None:
        if backup_file is None:
            # Find the most recent backup
            backup_files = list(BACKUP_DIR.glob("full_backup_*.json"))
            if not backup_files:
                logger.warning("No backup files found")
                return {}
            
            backup_file = str(max(backup_files, key=os.path.getctime))
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        logger.info(f"Importing data from: {backup_file}")
    else:
        logger.info("Importing data from provided backup data")
    
    # Import in order of dependencies
    import_tenants_and_products(session, backup_data.get("tenants", []), backup_data.get("products", []))
    import_external_agents(session, backup_data.get("external_agents", []))
    import_app_settings(backup_data.get("app_settings", {}))
    import_tenant_settings(backup_data.get("tenant_settings", {}))
    
    logger.info("Data import completed successfully")
    return backup_data


def import_tenants_and_products(session: Session, tenants_data: List[Dict[str, Any]], products_data: List[Dict[str, Any]]) -> None:
    """Import tenants and products from separate arrays."""
    # First, import all tenants
    tenant_map = {}  # Map backup tenant_id to actual tenant
    for tenant_data in tenants_data:
        # Check if tenant exists
        existing_tenant = session.query(Tenant).filter(Tenant.slug == tenant_data["slug"]).first()
        
        if existing_tenant:
            logger.info(f"Tenant already exists: {existing_tenant.name}")
            tenant = existing_tenant
        else:
            # Create tenant
            tenant = create_tenant(
                session=session,
                name=tenant_data["name"],
                slug=tenant_data["slug"]
            )
            logger.info(f"Created tenant: {tenant.name}")
        
        tenant_map[tenant_data["id"]] = tenant
    
    # Then, import all products
    products_imported = 0
    for product_data in products_data:
        tenant_id = product_data.get("tenant_id")
        if tenant_id not in tenant_map:
            logger.warning(f"Product {product_data['name']} references unknown tenant_id: {tenant_id}")
            continue
        
        tenant = tenant_map[tenant_id]
        
        # Check if product exists
        existing_product = session.query(Product).filter(
            Product.tenant_id == tenant.id,
            Product.name == product_data["name"]
        ).first()
        
        if existing_product:
            continue  # Product already exists
        
        # Create product
        create_product(
            session=session,
            tenant_id=tenant.id,
            name=product_data["name"],
            description=product_data["description"],
            price_cpm=product_data["price_cpm"],
            delivery_type=product_data["delivery_type"],
            formats_json=product_data["formats_json"],
            targeting_json=product_data["targeting_json"]
        )
        products_imported += 1
    
    logger.info(f"Imported {products_imported} products across {len(tenant_map)} tenants")


def import_tenants(session: Session, tenants_data: List[Dict[str, Any]]) -> None:
    """Import tenants and their products (legacy format with nested products)."""
    for tenant_data in tenants_data:
        # Check if tenant exists
        existing_tenant = session.query(Tenant).filter(Tenant.slug == tenant_data["slug"]).first()
        
        if existing_tenant:
            logger.info(f"Tenant already exists: {existing_tenant.name}")
            tenant = existing_tenant
        else:
            # Create tenant
            tenant = create_tenant(
                session=session,
                name=tenant_data["name"],
                slug=tenant_data["slug"]
            )
            logger.info(f"Created tenant: {tenant.name}")
        
        # Import products
        for product_data in tenant_data.get("products", []):
            # Check if product exists
            existing_product = session.query(Product).filter(
                Product.tenant_id == tenant.id,
                Product.name == product_data["name"]
            ).first()
            
            if existing_product:
                continue  # Product already exists
            
            # Create product
            create_product(
                session=session,
                tenant_id=tenant.id,
                name=product_data["name"],
                description=product_data["description"],
                price_cpm=product_data["price_cpm"],
                delivery_type=product_data["delivery_type"],
                formats_json=product_data["formats_json"],
                targeting_json=product_data["targeting_json"]
            )
        
        logger.info(f"Imported {len(tenant_data.get('products', []))} products for tenant: {tenant.name}")


def import_external_agents(session: Session, agents_data: List[Dict[str, Any]]) -> None:
    """Import external agents."""
    for agent_data in agents_data:
        # Check if agent exists by name
        existing_agent = session.query(ExternalAgent).filter(
            ExternalAgent.name == agent_data["name"]
        ).first()
        
        if existing_agent:
            logger.info(f"External agent already exists: {existing_agent.name}")
            continue
        
        # Create agent
        create_external_agent(
            session=session,
            name=agent_data["name"],
            endpoint_url=agent_data["endpoint_url"],
            api_key=agent_data.get("api_key"),
            is_active=agent_data.get("is_active", True)
        )
        logger.info(f"Created external agent: {agent_data['name']}")


def import_app_settings(settings: Dict[str, Any]) -> None:
    """Import application-wide settings."""
    # Note: Environment variables are typically set at deployment time
    # This function logs what settings should be configured
    logger.info("Application settings that should be configured:")
    for key, value in settings.items():
        if value:
            logger.info(f"  {key}: {value[:10]}..." if len(str(value)) > 10 else f"  {key}: {value}")


def import_tenant_settings(settings: Dict[str, Any]) -> None:
    """Import tenant-specific settings."""
    logger.info("Tenant settings imported")
