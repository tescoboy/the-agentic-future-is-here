"""Agent calling functions for orchestrator."""

import asyncio
import logging
from typing import Dict, Any

from app.services.mcp_client import MCPClient
from app.services.sales_contract import SALES_METHOD, build_sales_params
from app.services.signals_contract import SIG_METHOD, build_signals_params
from app.services.adapters.signals_response import normalize_signals
from app.services._orchestrator_breaker import (
    check_circuit_breaker, record_circuit_breaker_failure, reset_circuit_breaker
)
from app.models import ExternalAgent

logger = logging.getLogger(__name__)


async def call_sales_agent(tenant: Any, brief: str, semaphore: asyncio.Semaphore, config: Dict[str, Any], 
                          tenant_prompt: str = None, prompt_source: str = "default") -> Dict[str, Any]:
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
            
            # Call MCP agent
            client = MCPClient(base_url, timeout=config["timeout_ms"])
            try:
                await client.open()
                result = await client.call(SALES_METHOD, build_sales_params(brief, tenant_prompt))
                items = result.get("items", [])
                
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

