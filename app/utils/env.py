"""Environment utility functions."""

import os


def get_service_base_url() -> str:
    """
    Get service base URL with validation.
    
    Returns:
        Service base URL with trailing slash removed
        
    Raises:
        ValueError: If SERVICE_BASE_URL doesn't start with http:// or https://
    """
    url = os.getenv("SERVICE_BASE_URL", "http://localhost:8000").strip().rstrip("/")
    if not url.startswith(("http://", "https://")):
        raise ValueError("SERVICE_BASE_URL must start with http:// or https://")
    return url
