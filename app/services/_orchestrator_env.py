"""Environment configuration for orchestrator."""

import os
from typing import Dict, Any


def get_env_config() -> Dict[str, Any]:
    """Get environment configuration for orchestrator."""
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    
    env_timeout = os.getenv("ORCH_TIMEOUT_MS_DEFAULT", "25000")
    timeout_ms = int(env_timeout)
    
    # TEMPORARY FIX: Hardcode to 5 minutes while debugging env var issue
    if timeout_ms == 25000:
        timeout_ms = 300000  # 5 minutes
        logger.warning(f"ORCH_DEBUG: Using hardcoded 5-minute timeout due to env var issue")
    
    logger.info(f"ORCH_DEBUG: ORCH_TIMEOUT_MS_DEFAULT env value: {env_timeout}")
    logger.info(f"ORCH_DEBUG: Parsed timeout_ms: {timeout_ms}")
    
    return {
        "timeout_ms": timeout_ms,
        "concurrency": int(os.getenv("ORCH_CONCURRENCY", "8")),
        "cb_fails": int(os.getenv("CB_FAILS", "2")),
        "cb_ttl_s": int(os.getenv("CB_TTL_S", "60")),
        "service_base_url": os.getenv("SERVICE_BASE_URL", "http://localhost:8000")
    }

