"""
Embeddings configuration and environment validation.
Handles provider setup, API keys, and operational parameters.
"""

import os
from typing import Optional, Dict, Any


def get_embeddings_config() -> Dict[str, Any]:
    """
    Get embeddings configuration with validation and clamping.
    
    Returns:
        Configuration dict with all embedding settings
        
    Raises:
        RuntimeError: If provider configured but API key missing
    """
    provider = os.environ.get('EMBEDDINGS_PROVIDER', '').strip()
    
    config = {
        'enabled': bool(provider),
        'provider': provider,
        'model': os.environ.get('EMBEDDINGS_MODEL', 'text-embedding-004'),
        'api_key': None,
        'concurrency': _clamp_concurrency(),
        'batch_size': _clamp_batch_size()
    }
    
    # Validate API key if provider is set
    if config['enabled']:
        if provider == 'gemini':
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                raise RuntimeError("embeddings provider configured but GEMINI_API_KEY missing")
            config['api_key'] = api_key
        else:
            raise RuntimeError(f"unsupported embeddings provider: {provider}")
    
    return config


def is_embeddings_enabled() -> bool:
    """
    Check if embeddings are enabled.
    
    Returns:
        True if embeddings provider is configured
    """
    return bool(os.environ.get('EMBEDDINGS_PROVIDER', '').strip())


def validate_embeddings_setup() -> None:
    """
    Validate embeddings configuration.
    
    Raises:
        RuntimeError: If configuration is invalid
    """
    try:
        get_embeddings_config()
    except RuntimeError as e:
        raise RuntimeError(f"embeddings configuration error: {e}")


def _clamp_concurrency() -> int:
    """Clamp EMB_CONCURRENCY to valid range 1-8."""
    try:
        value = int(os.environ.get('EMB_CONCURRENCY', '2'))
        return max(1, min(8, value))
    except ValueError:
        return 2


def _clamp_batch_size() -> int:
    """Clamp EMB_BATCH_SIZE to valid range 1-128."""
    try:
        value = int(os.environ.get('EMB_BATCH_SIZE', '32'))
        return max(1, min(128, value))
    except ValueError:
        return 32
