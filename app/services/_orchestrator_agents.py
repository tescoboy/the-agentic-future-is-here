"""Agent calling functions for orchestrator."""

import asyncio
import logging
from typing import Dict, Any, Optional

from app.services.mcp_client import MCPClient
from app.services.sales_contract import SALES_METHOD, build_sales_params
from app.services.signals_contract import SIG_METHOD, build_signals_params
from app.services.adapters.signals_response import normalize_signals
from app.services._orchestrator_breaker import (
    check_circuit_breaker, record_circuit_breaker_failure, reset_circuit_breaker
)
from app.services.web_context_google import fetch_web_context
from app.models import ExternalAgent

logger = logging.getLogger(__name__)


async def call_sales_agent(tenant: Any, brief: str, semaphore: asyncio.Semaphore, config: Dict[str, Any], 
                          tenant_prompt: str = None, prompt_source: str = "default", 
                          web_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call internal Sales agent via MCP."""
    async with semaphore:
        try:
            base_url = f"{config['service_base_url']}/mcp/agents/{tenant.slug}/rpc"
            
            # Check circuit breaker
            if check_circuit_breaker(base_url):
                logger.info(f"agent={tenant.name} type=sales protocol=mcp ok=false keys=error")
                return {
                    "agent": {"name": tenant.name, "url": base_url, "type": "sales", "protocol": "mcp"},
                    "ok": False,
                    "items": None,
                    "error": "circuit breaker open"
                }
            
            # Handle web grounding if enabled
            web_snippets = None
            web_grounding_ok = True
            
            # DEBUG: Log web grounding configuration and tenant status
            logger.info(f"WEB_DEBUG: Starting web grounding check for tenant={tenant.slug}")
            logger.info(f"WEB_DEBUG: web_config received: {web_config}")
            logger.info(f"WEB_DEBUG: tenant.enable_web_context attribute exists: {hasattr(tenant, 'enable_web_context')}")
            if hasattr(tenant, 'enable_web_context'):
                logger.info(f"WEB_DEBUG: tenant.enable_web_context value: {tenant.enable_web_context}")
                logger.info(f"WEB_DEBUG: tenant.enable_web_context type: {type(tenant.enable_web_context)}")
            
            if web_config and web_config.get("enabled", False):
                logger.info(f"WEB_DEBUG: Global web grounding is ENABLED")
                # Check if tenant has web context enabled
                if hasattr(tenant, 'enable_web_context') and tenant.enable_web_context:
                    logger.info(f"WEB_DEBUG: Tenant web grounding is ENABLED - proceeding with web context fetch")
                    try:
                        logger.info(f"WEB_DEBUG: Calling fetch_web_context with timeout={web_config['timeout_ms']}, max_snippets={web_config['max_snippets']}, model={web_config['model']}, provider={web_config['provider']}")
                        # Prepare context for custom prompt
                        context = {
                            "brief": brief,
                            "tenant_name": tenant.name,
                            "tenant_slug": tenant.slug
                        }
                        
                        result = await fetch_web_context(
                            brief, 
                            web_config["timeout_ms"], 
                            web_config["max_snippets"],
                            web_config["model"],
                            web_config["provider"],
                            custom_prompt=getattr(tenant, 'web_grounding_prompt', None),
                            context=context
                        )
                        web_snippets = result["snippets"]
                        logger.info(f"WEB_DEBUG: Web context fetch successful, got {len(web_snippets)} snippets")
                        logger.info(f"web_grounding tenant={tenant.slug} enabled=1 model={web_config['model']} snippets={len(web_snippets)} ok=true")
                    except Exception as e:
                        web_grounding_ok = False
                        logger.error(f"WEB_DEBUG: Web context fetch failed with exception: {str(e)}")
                        logger.info(f"web_grounding tenant={tenant.slug} enabled=1 model={web_config['model']} snippets=0 ok=false")
                else:
                    logger.info(f"WEB_DEBUG: Tenant web grounding is DISABLED - skipping web context fetch")
                    logger.info(f"web_grounding tenant={tenant.slug} enabled=0 model={web_config['model']} snippets=0 ok=true")
            else:
                logger.info(f"WEB_DEBUG: Global web grounding is DISABLED - web_config={web_config}")
                logger.info(f"web_grounding tenant={tenant.slug} enabled=0 model=n/a snippets=0 ok=true")
            
            # Call MCP agent
            client = MCPClient(base_url, timeout=config["timeout_ms"])
            try:
                await client.open()
                
                # Add web snippets to sales params if available
                sales_params = build_sales_params(brief, tenant_prompt, web_snippets, result if web_snippets else None)
                
                result = await client.call(SALES_METHOD, sales_params)
                items = result.get("items", [])
                
                # Add web context error to items if grounding failed
                if not web_grounding_ok:
                    for item in items:
                        if "errors" not in item:
                            item["errors"] = []
                        item["errors"].append("web_context_unavailable")
                
                reset_circuit_breaker(base_url)
                logger.info(f"agent={tenant.name} type=sales protocol=mcp ok=true keys=items={len(items)} prompt_source={prompt_source}")
                
                return {
                    "agent": {"name": tenant.name, "url": base_url, "type": "sales", "protocol": "mcp"},
                    "ok": True,
                    "items": items,
                    "error": None
                }
            finally:
                await client.close()
                
        except Exception as e:
            record_circuit_breaker_failure(base_url, config)
            error_msg = f"timeout after {config['timeout_ms']}ms" if "timeout" in str(e).lower() else str(e)
            logger.info(f"agent={tenant.name} type=sales protocol=mcp ok=false keys=error")
            return {
                "agent": {"name": tenant.name, "url": base_url, "type": "sales", "protocol": "mcp"},
                "ok": False,
                "items": None,
                "error": error_msg
            }


async def call_signals_agent(agent: ExternalAgent, brief: str, semaphore: asyncio.Semaphore, config: Dict[str, Any]) -> Dict[str, Any]:
    """Call external Signals agent via MCP."""
    async with semaphore:
        try:
            # Validate protocol
            if agent.protocol != "mcp":
                logger.info(f"agent={agent.name} type=signals protocol={agent.protocol} ok=false keys=error")
                return {
                    "agent": {"name": agent.name, "url": agent.base_url, "type": "signals", "protocol": agent.protocol},
                    "ok": False,
                    "items": None,
                    "error": "signals requires protocol=mcp"
                }
            
            # Check circuit breaker
            if check_circuit_breaker(agent.base_url):
                logger.info(f"agent={agent.name} type=signals protocol=mcp ok=false keys=error")
                return {
                    "agent": {"name": agent.name, "url": agent.base_url, "type": "signals", "protocol": "mcp"},
                    "ok": False,
                    "items": None,
                    "error": "circuit breaker open"
                }
            
            # Special handling for Liveramp agent which has known issues
            if "audience-agent.fly.dev" in agent.base_url:
                logger.info(f"agent={agent.name} type=signals protocol=mcp ok=false keys=error")
                return {
                    "agent": {"name": agent.name, "url": agent.base_url, "type": "signals", "protocol": "mcp"},
                    "ok": False,
                    "items": None,
                    "error": "Liveramp agent temporarily unavailable - invalid request parameters"
                }
            
            # Call MCP agent
            client = MCPClient(agent.base_url, timeout=config["timeout_ms"])
            try:
                await client.open()
                result = await client.call(SIG_METHOD, build_signals_params(brief))
                items = normalize_signals(result)
                
                reset_circuit_breaker(agent.base_url)
                logger.info(f"agent={agent.name} type=signals protocol=mcp ok=true keys=items={len(items)}")
                
                return {
                    "agent": {"name": agent.name, "url": agent.base_url, "type": "signals", "protocol": "mcp"},
                    "ok": True,
                    "items": items,
                    "error": None
                }
            finally:
                await client.close()
                
        except Exception as e:
            record_circuit_breaker_failure(agent.base_url, config)
            error_msg = f"timeout after {config['timeout_ms']}ms" if "timeout" in str(e).lower() else str(e)
            logger.info(f"agent={agent.name} type=signals protocol=mcp ok=false keys=error")
            return {
                "agent": {"name": agent.name, "url": agent.base_url, "type": "signals", "protocol": "mcp"},
                "ok": False,
                "items": None,
                "error": error_msg
            }

