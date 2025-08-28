"""
Utilities for probing external agents (MCP and REST).
"""

import os
import logging
import httpx
from typing import Tuple

logger = logging.getLogger(__name__)


def is_debug_enabled() -> bool:
    """Check if DEBUG mode is enabled."""
    debug_val = os.getenv("DEBUG", "").lower()
    return debug_val in ["1", "true", "True"]


def log_probe(name: str, agent_type: str, protocol: str, url: str, outcome: str) -> None:
    """Log probe result with consistent format."""
    logger.info(f"Probe {name} ({agent_type}/{protocol}): {url} -> {outcome}")


def parse_probe_result(response: httpx.Response) -> Tuple[str, str]:
    """Parse probe response and categorize the result."""
    if response.status_code != 200:
        return "http_error", f"HTTP {response.status_code}: {response.text[:120]}"
    
    try:
        data = response.json()
        if "error" in data:
            error_msg = data["error"].get("message", "").lower()
            if "method not found" in error_msg:
                return "rpc_error", "Method not found"
            else:
                return "rpc_error", f"RPC error: {error_msg[:120]}"
        return "success", "Probe successful"
    except Exception:
        return "invalid_response", "Invalid JSON response"


async def probe_mcp_agent(base_url: str, timeout: int = 5) -> Tuple[str, str]:
    """Probe MCP agent with JSON-RPC initialize and mcp.get_info."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Try initialize first
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "adcp-demo",
                        "version": "0.1.0"
                    }
                }
            }
            headers = {"Accept": "application/json, text/event-stream"}
            init_response = await client.post(base_url, json=init_payload, headers=headers)
            
            if init_response.status_code != 200:
                return parse_probe_result(init_response)
            
            # Try mcp.get_info
            info_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "mcp.get_info",
                "params": {}
            }
            info_response = await client.post(base_url, json=info_payload, headers=headers)
            
            if info_response.status_code == 200:
                info_data = info_response.json()
                if "error" in info_data and "method not found" in info_data["error"].get("message", "").lower():
                    return "success", "MCP agent initialized (mcp.get_info not supported)"
                else:
                    return "success", "MCP agent responded successfully"
            else:
                return parse_probe_result(info_response)
                
    except httpx.TimeoutException:
        return "timeout", "Request timed out"
    except Exception as e:
        return "connection_error", str(e)[:120]


async def probe_rest_agent(base_url: str, timeout: int = 5) -> Tuple[str, str]:
    """Probe REST agent with connectivity test."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            payload = {"brief": "connectivity probe"}
            response = await client.post(base_url, json=payload)
            
            if response.status_code == 200:
                try:
                    response.json()  # Verify JSON response
                    return "success", "REST agent responded successfully"
                except Exception:
                    return "invalid_response", "Non-JSON response"
            else:
                return parse_probe_result(response)
                
    except httpx.TimeoutException:
        return "timeout", "Request timed out"
    except Exception as e:
        return "connection_error", str(e)[:120]


async def probe_external_agent(agent_type: str, protocol: str, base_url: str, name: str) -> Tuple[str, str]:
    """Probe external agent based on type and protocol."""
    if protocol == "mcp":
        category, message = await probe_mcp_agent(base_url)
    elif protocol == "rest":
        category, message = await probe_rest_agent(base_url)
    else:
        return "error", "Unknown protocol"
    
    # Log the probe result
    log_probe(name, agent_type, protocol, base_url, f"{category}: {message}")
    
    return category, message

