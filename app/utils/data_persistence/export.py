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


def export_tenants(session: Session) -> List[Dict[str, Any]]:
    """Export all tenants and their products."""
    tenants_data = []
    
    # Get all tenants using SQLModel
    tenants = session.exec(select(Tenant)).all()
    
    for tenant in tenants:
        # Get products for this tenant using SQLModel
        products = session.exec(select(Product).where(Product.tenant_id == tenant.id)).all()
        
        tenant_data = {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "custom_prompt": tenant.custom_prompt,
            "enable_web_context": tenant.enable_web_context,
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            "products": []
        }
        
        for product in products:
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
    
    logger.info(f"Exported {len(tenants)} tenants with {sum(len(t['products']) for t in tenants_data)} products")
    return tenants_data


def export_external_agents(session: Session) -> List[Dict[str, Any]]:
    """Export all external agents."""
    # Get all external agents using SQLModel
    agents = session.exec(select(ExternalAgent)).all()
    
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
    
    logger.info(f"Exported {len(agents_data)} external agents")
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
