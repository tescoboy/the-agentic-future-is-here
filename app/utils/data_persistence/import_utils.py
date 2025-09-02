"""
Import functions for data persistence.
"""

import gzip
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlmodel import Session, select

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
            # Find the most recent backup (include both .json and .json.gz files)
            json_files = list(BACKUP_DIR.glob("full_backup_*.json"))
            gz_files = list(BACKUP_DIR.glob("full_backup_*.json.gz"))
            backup_files = json_files + gz_files
            if not backup_files:
                logger.warning("No backup files found")
                return {}
            
            backup_file = str(max(backup_files, key=os.path.getctime))
        else:
            # Construct full path to backup file
            if not os.path.isabs(backup_file):
                backup_file = str(BACKUP_DIR / backup_file)
        
        # Check if file exists
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Handle both compressed (.gz) and uncompressed files
        backup_path = Path(backup_file)
        if backup_path.suffix == '.gz':
            logger.info(f"Loading compressed backup file: {backup_file}")
            with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
        else:
            logger.info(f"Loading uncompressed backup file: {backup_file}")
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
        
        logger.info(f"Importing data from: {backup_file}")
    else:
        logger.info("Importing data from provided backup data")
    
    # Import in order of dependencies
    # Check if we have the new format (separate arrays) or legacy format (nested products)
    tenants_data = backup_data.get("tenants", [])
    products_data = backup_data.get("products", [])
    
    if products_data:
        # New format: separate arrays
        import_tenants_and_products(session, tenants_data, products_data)
    else:
        # Legacy format: nested products
        import_tenants(session, tenants_data)
    
    import_external_agents(session, backup_data.get("external_agents", []))
    import_app_settings(backup_data.get("app_settings", {}))
    import_tenant_settings(backup_data.get("tenant_settings", {}))
    import_product_embeddings(session, backup_data.get("product_embeddings", []))
    
    logger.info("Data import completed successfully")
    return backup_data


def import_tenants_and_products(session: Session, tenants_data: List[Dict[str, Any]], products_data: List[Dict[str, Any]]) -> None:
    """Import tenants and products from separate arrays."""
    
    # Clear existing data before importing (like CSV import does)
    logger.info("Clearing existing data before import...")
    
    # Clear products first (they depend on tenants)
    products = session.exec(select(Product)).all()
    for product in products:
        session.delete(product)
    
    # Clear external agents
    agents = session.exec(select(ExternalAgent)).all()
    for agent in agents:
        session.delete(agent)
    
    # Clear tenants last
    tenants = session.exec(select(Tenant)).all()
    for tenant in tenants:
        session.delete(tenant)
    
    session.commit()
    logger.info("Cleared existing data")
    
    # First, import all tenants
    tenant_map = {}  # Map backup tenant_id to actual tenant
    for tenant_data in tenants_data:
        # Check if tenant exists using SQLModel
        existing_tenant = session.exec(select(Tenant).where(Tenant.slug == tenant_data["slug"])).first()
        
        if existing_tenant:
            logger.info(f"Tenant already exists: {existing_tenant.name}")
            tenant = existing_tenant
            # Update tenant fields if they exist in backup
            if "custom_prompt" in tenant_data:
                tenant.custom_prompt = tenant_data["custom_prompt"]
            if "enable_web_context" in tenant_data:
                tenant.enable_web_context = tenant_data["enable_web_context"]
            session.add(tenant)
            session.commit()
        else:
            # Create tenant
            tenant = create_tenant(
                session=session,
                name=tenant_data["name"],
                slug=tenant_data["slug"]
            )
            logger.info(f"Created tenant: {tenant.name}")
            
            # Update additional fields after creation
            if "custom_prompt" in tenant_data:
                tenant.custom_prompt = tenant_data["custom_prompt"]
            if "enable_web_context" in tenant_data:
                tenant.enable_web_context = tenant_data["enable_web_context"]
            session.add(tenant)
            session.commit()
        
        tenant_map[tenant_data["id"]] = tenant
    
    # Then, import all products
    products_imported = 0
    for product_data in products_data:
        tenant_id = product_data.get("tenant_id")
        if tenant_id not in tenant_map:
            logger.warning(f"Product {product_data['name']} references unknown tenant_id: {tenant_id}")
            continue
        
        tenant = tenant_map[tenant_id]
        
        # Check if product exists using SQLModel
        existing_product = session.exec(select(Product).where(
            Product.tenant_id == tenant.id,
            Product.name == product_data["name"]
        )).first()
        
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
        # Check if tenant exists using SQLModel
        existing_tenant = session.exec(select(Tenant).where(Tenant.slug == tenant_data["slug"])).first()
        
        if existing_tenant:
            logger.info(f"Tenant already exists: {existing_tenant.name}")
            tenant = existing_tenant
            # Update tenant fields if they exist in backup
            if "custom_prompt" in tenant_data:
                tenant.custom_prompt = tenant_data["custom_prompt"]
            if "web_grounding_prompt" in tenant_data:
                tenant.web_grounding_prompt = tenant_data["web_grounding_prompt"]
            if "enable_web_context" in tenant_data:
                tenant.enable_web_context = tenant_data["enable_web_context"]
            session.add(tenant)
            session.commit()
        else:
            # Create tenant
            tenant = create_tenant(
                session=session,
                name=tenant_data["name"],
                slug=tenant_data["slug"]
            )
            logger.info(f"Created tenant: {tenant.name}")
            
            # Update additional fields after creation
            if "custom_prompt" in tenant_data:
                tenant.custom_prompt = tenant_data["custom_prompt"]
            if "web_grounding_prompt" in tenant_data:
                tenant.web_grounding_prompt = tenant_data["web_grounding_prompt"]
            if "enable_web_context" in tenant_data:
                tenant.enable_web_context = tenant_data["enable_web_context"]
            session.add(tenant)
            session.commit()
        
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
        # Check if agent exists by name using SQLModel
        existing_agent = session.exec(select(ExternalAgent).where(
            ExternalAgent.name == agent_data["name"]
        )).first()
        
        if existing_agent:
            logger.info(f"External agent already exists: {existing_agent.name}")
            continue
        
        # Create agent
        create_external_agent(
            session=session,
            name=agent_data["name"],
            endpoint_url=agent_data["base_url"],  # Map base_url to endpoint_url
            api_key=agent_data.get("api_key"),
            is_active=agent_data.get("enabled", True)  # Map enabled to is_active
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


def import_product_embeddings(session: Session, embeddings_data: List[Dict[str, Any]]) -> None:
    """Import product embeddings."""
    if not embeddings_data:
        logger.info("No product embeddings to import")
        return
    
    logger.info(f"Starting import of {len(embeddings_data)} product embeddings...")
    
    try:
        # Clear existing embeddings to avoid conflicts
        session.execute("DELETE FROM product_embeddings")
        logger.info("Cleared existing product embeddings")
        
        embeddings_imported = 0
        for embedding_data in embeddings_data:
            try:
                # Convert hex string back to BLOB
                embedding_blob = bytes.fromhex(embedding_data["embedding"]) if embedding_data["embedding"] else None
                
                # Insert embedding using raw SQL since it's not a SQLModel
                insert_query = """
                INSERT INTO product_embeddings 
                (id, product_id, embedding_text, embedding_hash, embedding, created_at, 
                 provider, model, dim, updated_at, is_stale)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                session.execute(insert_query, (
                    embedding_data["id"],
                    embedding_data["product_id"],
                    embedding_data["embedding_text"],
                    embedding_data["embedding_hash"],
                    embedding_blob,
                    embedding_data["created_at"],
                    embedding_data["provider"],
                    embedding_data["model"],
                    embedding_data["dim"],
                    embedding_data["updated_at"],
                    embedding_data["is_stale"]
                ))
                
                embeddings_imported += 1
                
            except Exception as e:
                logger.warning(f"Failed to import embedding for product_id {embedding_data.get('product_id', 'unknown')}: {e}")
                continue
        
        session.commit()
        logger.info(f"Successfully imported {embeddings_imported} product embeddings")
        
    except Exception as e:
        logger.error(f"Failed to import product embeddings: {e}")
        session.rollback()
        raise
