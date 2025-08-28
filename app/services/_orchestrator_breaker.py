"""Circuit breaker logic for orchestrator."""

import time
from typing import Dict, Any


# Circuit breaker state (in-memory)
_circuit_breakers: Dict[str, Dict] = {}


def check_circuit_breaker(base_url: str) -> bool:
    """Check if circuit breaker is open for the given base_url."""
    if base_url not in _circuit_breakers:
        return False
    
    breaker = _circuit_breakers[base_url]
    if breaker.get("tripped_until", 0) > time.monotonic():
        return True
    
    # Reset if cooldown expired
    if "tripped_until" in breaker:
        del breaker["tripped_until"]
    return False


def record_circuit_breaker_failure(base_url: str, config: Dict[str, Any]) -> None:
    """Record a failure for circuit breaker."""
    if base_url not in _circuit_breakers:
        _circuit_breakers[base_url] = {"fails": 0}
    
    breaker = _circuit_breakers[base_url]
    breaker["fails"] += 1
    
    if breaker["fails"] >= config["cb_fails"]:
        breaker["tripped_until"] = time.monotonic() + config["cb_ttl_s"]


def reset_circuit_breaker(base_url: str) -> None:
    """Reset circuit breaker on success."""
    if base_url in _circuit_breakers:
        _circuit_breakers[base_url]["fails"] = 0
        if "tripped_until" in _circuit_breakers[base_url]:
            del _circuit_breakers[base_url]["tripped_until"]

