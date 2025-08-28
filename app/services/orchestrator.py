"""Orchestrator service for fanning out buyer briefs to agents."""

import asyncio
import logging
from typing import Dict, List, Any

from app.repos.tenants import get_tenant_by_id
from app.services.mcp_client import MCPClient
from app.services.sales_contract import SALES_METHOD, build_sales_params
from app.services.signals_contract import SIG_METHOD, build_signals_params
from app.services.adapters.signals_response import normalize_signals
from app.services._orchestrator_env import get_env_config
from app.services._orchestrator_agents import call_sales_agent, call_signals_agent
from app.models import ExternalAgent
from app.db import get_session

logger = logging.getLogger(__name__)


async def orchestrate_brief(brief: str, tenant_ids: List[int], external_agents: List[ExternalAgent]) -> Dict[str, Any]:
    """
    Orchestrate buyer brief to internal and external agents.
    
    Args:
        brief: Buyer brief string
        tenant_ids: List of tenant IDs for internal Sales agents
        external_agents: List of external agents (Signals only)
        
    Returns:
        Structured results with sales and signals entries
    """
    if not brief or not brief.strip():
        raise ValueError("brief cannot be empty")
    
    config = get_env_config()
    semaphore = asyncio.Semaphore(config["concurrency"])
    
    # Create sales tasks
    sales_tasks = []
    
    for tenant_id in tenant_ids:
        # Get tenant for custom prompt lookup
        with next(get_session()) as db_session:
            tenant = get_tenant_by_id(db_session, tenant_id)
            if not tenant:
                logger.warning(f"Tenant {tenant_id} not found, skipping")
                continue
            
            # Use tenant's custom prompt if available, otherwise default
            tenant_prompt = tenant.custom_prompt if tenant.custom_prompt else None
            prompt_source = "custom" if tenant.custom_prompt else "default"
            
            task = asyncio.create_task(call_sales_agent(tenant, brief, semaphore, config, tenant_prompt, prompt_source))
            sales_tasks.append(task)
    
    # Create signals tasks
    signals_tasks = [
        asyncio.create_task(call_signals_agent(agent, brief, semaphore, config))
        for agent in external_agents
    ]
    
    # Execute all tasks concurrently
    all_tasks = sales_tasks + signals_tasks
    results = await asyncio.gather(*all_tasks, return_exceptions=False)
    
    # Separate results
    sales_results = results[:len(sales_tasks)]
    signals_results = results[len(sales_tasks):]
    
    return {
        "results": sales_results,
        "signals": signals_results
    }
