"""Signals response normalization adapter."""

from typing import List, Dict, Any


def normalize_signals(result_obj: dict) -> List[Dict[str, Any]]:
    """
    Normalize signals response from MCP signals agent.
    
    Args:
        result_obj: JSON-RPC result object from signals agent
        
    Returns:
        List of normalized signal objects
        
    Raises:
        ValueError: If no valid signals found or invalid response structure
    """
    # Extract signals using documented key from reference repo
    # Based on signals-agent reference at commit <ce1081c>
    # Key documented in the reference repo's response format
    signals = result_obj.get("signals")
    
    if not signals or not isinstance(signals, list):
        available_keys = list(result_obj.keys())
        raise ValueError(f"invalid_response: no valid signals found; keys={available_keys}")
    
    normalized = []
    for signal in signals:
        if not isinstance(signal, dict):
            continue
            
        # Extract required fields based on reference repo structure
        signal_id = signal.get("id") or signal.get("signal_id")
        name = signal.get("name") or signal.get("title")
        reason = signal.get("reason") or signal.get("description")
        score = signal.get("score")
        
        # Validate required fields
        if not signal_id or not name:
            continue
            
        normalized.append({
            "signal_id": str(signal_id),
            "name": str(name),
            "reason": str(reason) if reason else "",
            "score": float(score) if score is not None else None
        })
    
    if not normalized:
        available_keys = list(result_obj.keys())
        raise ValueError(f"invalid_response: no valid signals found; keys={available_keys}")
    
    return normalized

