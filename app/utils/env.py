"""
Environment variable utilities.
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


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
    # DEBUG: Log all environment variables related to web grounding
    logger.info("WEB_DEBUG: Loading web grounding configuration from environment variables")
    logger.info(f"WEB_DEBUG: ENABLE_WEB_CONTEXT raw value: '{os.environ.get('ENABLE_WEB_CONTEXT', 'NOT_SET')}'")
    logger.info(f"WEB_DEBUG: WEB_CONTEXT_TIMEOUT_MS raw value: '{os.environ.get('WEB_CONTEXT_TIMEOUT_MS', 'NOT_SET')}'")
    logger.info(f"WEB_DEBUG: WEB_CONTEXT_MAX_SNIPPETS raw value: '{os.environ.get('WEB_CONTEXT_MAX_SNIPPETS', 'NOT_SET')}'")
    logger.info(f"WEB_DEBUG: GEMINI_MODEL raw value: '{os.environ.get('GEMINI_MODEL', 'NOT_SET')}'")
    
    # Read environment variables
    enabled_str = os.environ.get('ENABLE_WEB_CONTEXT', '0')
    timeout_ms_str = os.environ.get('WEB_CONTEXT_TIMEOUT_MS', '2000')
    max_snippets_str = os.environ.get('WEB_CONTEXT_MAX_SNIPPETS', '3')
    model = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    
    # Validate and convert enabled flag
    if enabled_str.lower() in ('1', 'true', 'yes', 'on'):
        enabled = True
        logger.info("WEB_DEBUG: ENABLE_WEB_CONTEXT parsed as ENABLED")
    elif enabled_str.lower() in ('0', 'false', 'no', 'off'):
        enabled = False
        logger.info("WEB_DEBUG: ENABLE_WEB_CONTEXT parsed as DISABLED")
    else:
        logger.error(f"WEB_DEBUG: ENABLE_WEB_CONTEXT has invalid value: '{enabled_str}'")
        raise ValueError("ENABLE_WEB_CONTEXT must be 0/1, true/false, yes/no, or on/off")
    
    # Validate and convert timeout
    try:
        timeout_ms = int(timeout_ms_str)
        logger.info(f"WEB_DEBUG: WEB_CONTEXT_TIMEOUT_MS parsed as: {timeout_ms}")
    except ValueError:
        logger.error(f"WEB_DEBUG: WEB_CONTEXT_TIMEOUT_MS has invalid value: '{timeout_ms_str}'")
        raise ValueError("WEB_CONTEXT_TIMEOUT_MS must be a valid integer")
    
    # Validate and convert max snippets
    try:
        max_snippets = int(max_snippets_str)
        logger.info(f"WEB_DEBUG: WEB_CONTEXT_MAX_SNIPPETS parsed as: {max_snippets}")
    except ValueError:
        logger.error(f"WEB_DEBUG: WEB_CONTEXT_MAX_SNIPPETS has invalid value: '{max_snippets_str}'")
        raise ValueError("WEB_CONTEXT_MAX_SNIPPETS must be a valid integer")
    
    # Determine provider based on model
    if model.startswith('gemini-1.5-'):
        provider = "google_search_retrieval"
    else:
        provider = "google_search"
    
    logger.info(f"WEB_DEBUG: GEMINI_MODEL parsed as: {model}")
    logger.info(f"WEB_DEBUG: Provider determined as: {provider}")
    
    config = {
        "enabled": enabled,
        "timeout_ms": timeout_ms,
        "max_snippets": max_snippets,
        "model": model,
        "provider": provider
    }
    
    logger.info(f"WEB_DEBUG: Final web grounding config: {config}")
    return config
