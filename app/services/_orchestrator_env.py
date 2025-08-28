"""Environment configuration for orchestrator."""

import os
from typing import Dict, Any


def get_env_config() -> Dict[str, Any]:
    """Get environment configuration for orchestrator."""
    return {
        "timeout_ms": int(os.getenv("ORCH_TIMEOUT_MS_DEFAULT", "25000")),
        "concurrency": int(os.getenv("ORCH_CONCURRENCY", "8")),
        "cb_fails": int(os.getenv("CB_FAILS", "2")),
        "cb_ttl_s": int(os.getenv("CB_TTL_S", "60")),
        "service_base_url": os.getenv("SERVICE_BASE_URL", "http://localhost:8000")
    }

