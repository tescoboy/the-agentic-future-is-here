"""
Environment variable utilities.
"""

import os
from typing import Optional


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
