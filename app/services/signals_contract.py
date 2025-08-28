"""
Signals Agent Contract Constants
Repo: reference/signals-agent
Commit: ce1081c
File: client.py (line 103)
Method: get_signals(request_data: dict)
"""

from app.services._contract_utils import get_signalsagent_commit

# Method name from reference repository
SIG_METHOD = "get_signals"


def build_signals_params(brief: str) -> dict:
    """
    Build parameters for signals agent request.
    
    Args:
        brief: The signal specification description
        
    Returns:
        Dictionary with required parameters for signals agent
        
    Raises:
        ValueError: If brief is empty
    """
    if not brief or not brief.strip():
        raise ValueError("brief cannot be empty")
    
    # Return minimal required structure from reference contract
    # Based on client.py line 103 - get_signals expects signal_spec
    return {
        "signal_spec": brief.strip()
    }

