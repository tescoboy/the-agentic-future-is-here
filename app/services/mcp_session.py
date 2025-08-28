"""MCP session management with TTL-based expiry."""

import logging
import os
import time
import uuid
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MCPSessionStore:
    """In-memory session store with TTL-based expiry."""
    
    def __init__(self, ttl: int = None):
        """Initialize session store with TTL in seconds."""
        self._sessions: Dict[str, Dict] = {}
        self._tenant_sessions: Dict[str, str] = {}  # tenant_slug -> session_id
        self._ttl = ttl or self._get_ttl()
    
    def _get_ttl(self) -> int:
        """Get TTL from environment or default to 60 seconds."""
        # Try MCP_SESSION_TTL_S first, then fall back to ORCH_TIMEOUT_MS_DEFAULT/1000
        ttl_s = os.getenv('MCP_SESSION_TTL_S')
        if ttl_s:
            try:
                return int(ttl_s)
            except ValueError:
                logger.warning(f"Invalid MCP_SESSION_TTL_S: {ttl_s}, using default")
        
        # Fall back to ORCH_TIMEOUT_MS_DEFAULT/1000, minimum 60s
        orch_timeout = os.getenv('ORCH_TIMEOUT_MS_DEFAULT')
        if orch_timeout:
            try:
                return max(60, int(orch_timeout) // 1000)
            except ValueError:
                logger.warning(f"Invalid ORCH_TIMEOUT_MS_DEFAULT: {orch_timeout}, using default")
        
        return 60
    
    def create_session(self, tenant_slug: str) -> str:
        """Create a new session for the given tenant."""
        session_id = str(uuid.uuid4())
        expires_at = time.monotonic() + self._ttl
        
        self._sessions[session_id] = {
            "tenant_slug": tenant_slug,
            "expires_at": expires_at
        }
        
        # Track that this tenant has a session
        self._tenant_sessions[tenant_slug] = session_id
        
        logger.info(f"mcp session create tenant={tenant_slug} id={session_id[:8]}")
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[str]:
        """Validate session and return tenant_slug if valid, None if expired/invalid."""
        if session_id not in self._sessions:
            return None
        
        session_data = self._sessions[session_id]
        if time.monotonic() > session_data["expires_at"]:
            # Session expired, remove it
            tenant_slug = session_data["tenant_slug"]
            del self._sessions[session_id]
            if tenant_slug in self._tenant_sessions:
                del self._tenant_sessions[tenant_slug]
            logger.warning(f"mcp session invalid id={session_id[:8]} (expired)")
            return None
        
        return session_data["tenant_slug"]
    
    def has_session_for_tenant(self, tenant_slug: str) -> bool:
        """Check if tenant has an active session."""
        if tenant_slug not in self._tenant_sessions:
            return False
        
        session_id = self._tenant_sessions[tenant_slug]
        return self.validate_session(session_id) is not None
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        if session_id in self._sessions:
            tenant_slug = self._sessions[session_id]["tenant_slug"]
            del self._sessions[session_id]
            if tenant_slug in self._tenant_sessions:
                del self._tenant_sessions[tenant_slug]
            logger.info(f"mcp session delete id={session_id[:8]}")


# Module-level singleton
session_store = MCPSessionStore()
