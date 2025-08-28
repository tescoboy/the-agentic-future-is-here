"""
Contract utilities for caching reference repository commit hashes.
"""

from typing import Dict, Optional

# Cache for commit hashes from Phase 1 validator
_commit_cache: Optional[Dict[str, str]] = None


def _load_commit_cache() -> Dict[str, str]:
    """Load commit hashes from Phase 1 validator once at startup."""
    global _commit_cache
    if _commit_cache is None:
        from app.utils.reference_validator import validate_reference_repos
        try:
            _commit_cache = validate_reference_repos()
        except Exception:
            # Fallback if validator fails
            _commit_cache = {
                'salesagent': '0a0403c',
                'signals-agent': 'ce1081c'
            }
    return _commit_cache


def get_salesagent_commit() -> str:
    """Get the short commit hash for the salesagent repository."""
    cache = _load_commit_cache()
    return cache.get('salesagent', '0a0403c')


def get_signalsagent_commit() -> str:
    """Get the short commit hash for the signals-agent repository."""
    cache = _load_commit_cache()
    return cache.get('signals-agent', 'ce1081c')

