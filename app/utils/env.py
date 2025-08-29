"""
Environment variable utilities.
"""

import os
from typing import Optional, Dict, Any


def get_gemini_api_key() -> Optional[str]:
    """
    Get Gemini API key from environment variable.
    
    Returns:
        API key if set, None otherwise
    """
    return os.environ.get('GEMINI_API_KEY')


def get_service_base_url() -> str:
    """
    Get service base URL from environment variable.
    
    Returns:
        Service base URL (default: http://localhost:8000)
    """
    base_url = os.environ.get('SERVICE_BASE_URL', 'http://localhost:8000')
    # Strip whitespace and trailing slashes
    base_url = base_url.strip().rstrip('/')
    
    # Validate scheme
    if not base_url.startswith(('http://', 'https://')):
        raise ValueError("SERVICE_BASE_URL must start with http:// or https://")
    
    return base_url


def get_web_grounding_config() -> Dict[str, Any]:
    """
    Get web grounding configuration from environment variables.
    
    Returns:
        Configuration dict with enabled, timeout_ms, max_snippets, model, provider
        
    Raises:
        ValueError: If configuration values are invalid
    """
    # Read environment variables
    enabled_str = os.environ.get('ENABLE_WEB_CONTEXT', '0')
    timeout_ms_str = os.environ.get('WEB_CONTEXT_TIMEOUT_MS', '2000')
    max_snippets_str = os.environ.get('WEB_CONTEXT_MAX_SNIPPETS', '3')
    model = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    
    # Validate and convert enabled flag
    if enabled_str.lower() in ('1', 'true', 'yes', 'on'):
        enabled = True
    elif enabled_str.lower() in ('0', 'false', 'no', 'off'):
        enabled = False
    else:
        raise ValueError("ENABLE_WEB_CONTEXT must be 0/1, true/false, yes/no, or on/off")
    
    # Validate and convert timeout
    try:
        timeout_ms = int(timeout_ms_str)
        if timeout_ms < 100 or timeout_ms > 10000:
            raise ValueError("WEB_CONTEXT_TIMEOUT_MS must be between 100 and 10000")
    except ValueError:
        raise ValueError("WEB_CONTEXT_TIMEOUT_MS must be a valid integer")
    
    # Validate and convert max snippets
    try:
        max_snippets = int(max_snippets_str)
        if max_snippets < 1 or max_snippets > 10:
            raise ValueError("WEB_CONTEXT_MAX_SNIPPETS must be between 1 and 10")
    except ValueError:
        raise ValueError("WEB_CONTEXT_MAX_SNIPPETS must be a valid integer")
    
    # Determine provider based on model
    if model.startswith('gemini-1.5-'):
        provider = "google_search_retrieval"
    else:
        provider = "google_search"
    
    return {
        "enabled": enabled,
        "timeout_ms": timeout_ms,
        "max_snippets": max_snippets,
        "model": model,
        "provider": provider
    }
