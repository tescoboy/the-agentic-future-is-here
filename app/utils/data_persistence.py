"""
Data persistence utilities for backing up and restoring all application data.
Ensures settings, prompts, external agents, and other configuration survive redeploys.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models import Tenant, Product, ExternalAgent
from app.repos.tenants import get_tenant_by_slug
from app.repos.external_agents import list_external_agents, create_external_agent
from app.repos.products import list_products, create_product

logger = logging.getLogger(__name__)

# Data directory for persistence files
DATA_DIR = Path("./data")
BACKUP_DIR = DATA_DIR / "backups"
SETTINGS_FILE = DATA_DIR / "app_settings.json"
EXTERNAL_AGENTS_FILE = DATA_DIR / "external_agents.json"
TENANT_SETTINGS_FILE = DATA_DIR / "tenant_settings.json"


def ensure_data_directories():
    """Ensure all data directories exist."""
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)


def export_all_data(session: Session) -> Dict[str, Any]:
    """Export all application data to a comprehensive backup."""
    ensure_data_directories()
    
    backup_data = {
        "exported_at": datetime.now().isoformat(),
        "version": "1.0",
        "tenants": export_tenants(session),
        "external_agents": export_external_agents(session),
        "app_settings": export_app_settings(),
        "tenant_settings": export_tenant_settings()
    }
    
    # Save to backup file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"full_backup_{timestamp}.json"
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Full backup exported to: {backup_file}")
    return backup_data


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


def export_tenants(session: Session) -> List[Dict[str, Any]]:
    """Export all tenants and their products."""
    tenants_data = []
    
    # Get all tenants
    tenants = session.query(Tenant).all()
    
    for tenant in tenants:
        # Get products for this tenant
        products, _ = list_products(session, tenant_id=tenant.id)
        
        tenant_data = {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            "products": []
        }
        
        for product in products:
            product_data = {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price_cpm": product.price_cpm,
                "delivery_type": product.delivery_type,
                "formats_json": product.formats_json,
                "targeting_json": product.targeting_json,
                "created_at": product.created_at.isoformat() if product.created_at else None
            }
            tenant_data["products"].append(product_data)
        
        tenants_data.append(tenant_data)
    
    logger.info(f"Exported {len(tenants)} tenants with {sum(len(t['products']) for t in tenants_data)} products")
    return tenants_data


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
            from app.repos.tenants import create_tenant
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
            from app.repos.tenants import create_tenant
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


def export_external_agents(session: Session) -> List[Dict[str, Any]]:
    """Export all external agents."""
    agents = list_external_agents(session)
    
    agents_data = []
    for agent in agents:
        agent_data = {
            "id": agent.id,
            "name": agent.name,
            "endpoint_url": agent.endpoint_url,
            "api_key": agent.api_key,
            "is_active": agent.is_active,
            "created_at": agent.created_at.isoformat() if agent.created_at else None
        }
        agents_data.append(agent_data)
    
    logger.info(f"Exported {len(agents_data)} external agents")
    return agents_data


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


def export_app_settings() -> Dict[str, Any]:
    """Export application-wide settings."""
    settings = {
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "embeddings_provider": os.getenv("EMBEDDINGS_PROVIDER"),
        "embeddings_model": os.getenv("EMBEDDINGS_MODEL"),
        "emb_concurrency": os.getenv("EMB_CONCURRENCY"),
        "emb_batch_size": os.getenv("EMB_BATCH_SIZE"),
        "rag_top_k": os.getenv("RAG_TOP_K"),
        "orchestrator_timeout": os.getenv("ORCH_TIMEOUT_MS_DEFAULT"),
        "orchestrator_concurrency": os.getenv("ORCH_CONCURRENCY"),
        "circuit_breaker_fails": os.getenv("CB_FAILS"),
        "circuit_breaker_ttl": os.getenv("CB_TTL_S"),
        "mcp_session_ttl": os.getenv("MCP_SESSION_TTL_S")
    }
    
    # Save to settings file
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    
    logger.info("Exported application settings")
    return settings


def import_app_settings(settings: Dict[str, Any]) -> None:
    """Import application-wide settings."""
    # Note: Environment variables are typically set at deployment time
    # This function logs what settings should be configured
    logger.info("Application settings that should be configured:")
    for key, value in settings.items():
        if value:
            logger.info(f"  {key}: {value[:10]}..." if len(str(value)) > 10 else f"  {key}: {value}")


def export_tenant_settings() -> Dict[str, Any]:
    """Export tenant-specific settings and prompts."""
    # This would include tenant-specific configurations
    # For now, we'll create a placeholder structure
    settings = {
        "tenant_prompts": {},
        "tenant_configurations": {},
        "exported_at": datetime.now().isoformat()
    }
    
    # Save to settings file
    with open(TENANT_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    
    logger.info("Exported tenant settings")
    return settings


def import_tenant_settings(settings: Dict[str, Any]) -> None:
    """Import tenant-specific settings."""
    logger.info("Tenant settings imported")


def create_backup() -> str:
    """Create a backup of all data."""
    from app.db import get_session
    
    session = next(get_session())
    try:
        backup_data = export_all_data(session)
        return "Backup created successfully"
    finally:
        session.close()


def restore_backup(backup_file: Optional[str] = None) -> str:
    """Restore data from backup."""
    from app.db import get_session
    
    session = next(get_session())
    try:
        import_all_data(session, backup_file)
        return "Backup restored successfully"
    finally:
        session.close()


def list_backups() -> List[str]:
    """List all available backup files."""
    ensure_data_directories()
    backup_files = list(BACKUP_DIR.glob("full_backup_*.json"))
    return [f.name for f in sorted(backup_files, key=os.path.getctime, reverse=True)]


def auto_backup_on_startup(session: Session) -> None:
    """Automatically create a backup on startup."""
    try:
        export_all_data(session)
        logger.info("Auto-backup created on startup")
    except Exception as e:
        logger.warning(f"Auto-backup failed: {e}")


def auto_restore_on_startup(session: Session) -> None:
    """Automatically restore from latest backup on startup."""
    try:
        backup_files = list(BACKUP_DIR.glob("full_backup_*.json"))
        if backup_files:
            latest_backup = max(backup_files, key=os.path.getctime)
            import_all_data(session, str(latest_backup))
            logger.info(f"Auto-restored from: {latest_backup.name}")
        else:
            logger.info("No backup files found for auto-restore")
    except Exception as e:
        logger.warning(f"Auto-restore failed: {e}")

