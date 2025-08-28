"""Form validation and handling utilities."""

from typing import Dict, Any


def validate_agent_type(agent_type: str) -> None:
    """Validate agent type."""
    if agent_type not in ["sales", "signals"]:
        raise ValueError("Agent type must be 'sales' or 'signals'")


def validate_protocol(protocol: str) -> None:
    """Validate protocol."""
    if protocol not in ["rest", "mcp"]:
        raise ValueError("Protocol must be 'rest' or 'mcp'")


def validate_base_url(base_url: str) -> None:
    """Validate base URL format."""
    if not base_url.startswith(("http://", "https://")):
        truncated_url = base_url[:200] if len(base_url) > 200 else base_url
        raise ValueError(f"base_url must start with http:// or https://. Got: {truncated_url}")


def validate_external_agent_form(name: str, base_url: str, agent_type: str, protocol: str) -> None:
    """Validate external agent form data."""
    validate_agent_type(agent_type)
    validate_protocol(protocol)
    validate_base_url(base_url)


def get_form_error_context(name: str, base_url: str, agent_type: str, protocol: str, enabled: bool) -> Dict[str, Any]:
    """Get form context for error display."""
    return {
        "name": name,
        "base_url": base_url,
        "agent_type": agent_type,
        "protocol": protocol,
        "enabled": enabled
    }

