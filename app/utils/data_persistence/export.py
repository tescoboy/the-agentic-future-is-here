"""
Export functions for data persistence.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any
from sqlmodel import Session, select

from app.models import Tenant, Product, ExternalAgent
from app.repos.tenants import get_tenant_by_slug
from app.repos.external_agents import list_external_agents
from app.repos.products import list_products
from .core import ensure_data_directories, BACKUP_DIR, SETTINGS_FILE, TENANT_SETTINGS_FILE

logger = logging.getLogger(__name__)


def export_all_data(session: Session) -> Dict[str, Any]:
    """Export all application data to a comprehensive backup."""
    logger.info("Starting JSON backup export...")
    ensure_data_directories()
    
    # Export data with progress logging
    logger.info("Exporting tenants and products...")
    tenants_data = export_tenants(session)
    
    logger.info("Exporting external agents...")
    external_agents_data = export_external_agents(session)
    
    logger.info("Exporting application settings...")
    app_settings_data = export_app_settings()
    
    logger.info("Exporting tenant settings...")
    tenant_settings_data = export_tenant_settings()
    
    # Compile backup data
    backup_data = {
        "exported_at": datetime.now().isoformat(),
        "version": "1.0",
        "tenants": tenants_data,
        "external_agents": external_agents_data,
        "app_settings": app_settings_data,
        "tenant_settings": tenant_settings_data
    }
    
    # Save to backup file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"full_backup_{timestamp}.json"
    
    logger.info(f"Writing backup file: {backup_file}")
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    # Calculate summary statistics
    total_tenants = len(tenants_data)
    total_products = sum(len(t['products']) for t in tenants_data)
    total_agents = len(external_agents_data)
    
    logger.info(f"JSON backup completed successfully!")
    logger.info(f"  - {total_tenants} tenants exported")
    logger.info(f"  - {total_products} products exported")
    logger.info(f"  - {total_agents} external agents exported")
    logger.info(f"  - Backup file: {backup_file}")
    
    return backup_data


def export_tenants(session: Session) -> List[Dict[str, Any]]:
    """Export all tenants and their products using bulk operations."""
    logger.info("Starting tenant and product export...")
    
    # Get all tenants in one query
    tenants = session.exec(select(Tenant)).all()
    logger.info(f"Found {len(tenants)} tenants")
    
    # Get all products in one query (much faster than per-tenant queries)
    all_products = session.exec(select(Product)).all()
    logger.info(f"Found {len(all_products)} total products")
    
    # Create product lookup by tenant_id for O(1) access
    products_by_tenant = {}
    for product in all_products:
        if product.tenant_id not in products_by_tenant:
            products_by_tenant[product.tenant_id] = []
        products_by_tenant[product.tenant_id].append(product)
    
    # Build tenant data with their products
    tenants_data = []
    for tenant in tenants:
        tenant_products = products_by_tenant.get(tenant.id, [])
        
        tenant_data = {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "custom_prompt": tenant.custom_prompt,
            "web_grounding_prompt": tenant.web_grounding_prompt,
            "enable_web_context": tenant.enable_web_context,
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            "products": []
        }
        
        # Convert products to dict format in bulk
        for product in tenant_products:
            product_data = {
                "id": product.id,
                "tenant_id": product.tenant_id,
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
    
    total_products = sum(len(t['products']) for t in tenants_data)
    logger.info(f"Completed tenant export: {len(tenants)} tenants, {total_products} products")
    return tenants_data


def export_external_agents(session: Session) -> List[Dict[str, Any]]:
    """Export all external agents using bulk operations."""
    logger.info("Starting external agent export...")
    
    # Get all external agents in one query
    agents = session.exec(select(ExternalAgent)).all()
    logger.info(f"Found {len(agents)} external agents")
    
    # Convert to dict format in bulk
    agents_data = []
    for agent in agents:
        agent_data = {
            "id": agent.id,
            "name": agent.name,
            "base_url": agent.base_url,
            "enabled": agent.enabled,
            "agent_type": agent.agent_type,
            "protocol": agent.protocol,
            "created_at": agent.created_at.isoformat() if agent.created_at else None
        }
        agents_data.append(agent_data)
    
    logger.info(f"Completed external agent export: {len(agents_data)} agents")
    return agents_data


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
