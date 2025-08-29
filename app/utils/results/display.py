"""Results display utilities."""

from typing import List, Dict, Any


def filter_items_by_score_threshold(items: List[Dict[str, Any]], threshold: float = 0.70) -> List[Dict[str, Any]]:
    """
    Filter items by score threshold.
    
    Args:
        items: List of items with optional 'score' field
        threshold: Minimum score threshold (default 0.70)
        
    Returns:
        Filtered list of items with score >= threshold
    """
    filtered = []
    for item in items:
        score = item.get("score")
        if score is not None and score >= threshold:
            filtered.append(item)
    return filtered


def generate_heat_indicator(score: float) -> str:
    """
    Generate heat indicator HTML for a given score.
    
    Args:
        score: Score value between 0.0 and 1.0
        
    Returns:
        HTML string with Font Awesome flame icons
    """
    if score < 0.70:
        return ""
    
    percentage = int(score * 100)
    
    if 70 <= percentage <= 79:
        return '<i class="fa-solid fa-fire text-warning"></i>'
    elif 80 <= percentage <= 89:
        return '<i class="fa-solid fa-fire text-warning"></i><i class="fa-solid fa-fire text-warning"></i>'
    elif 90 <= percentage <= 97:
        return '<i class="fa-solid fa-fire text-danger"></i><i class="fa-solid fa-fire text-danger"></i><i class="fa-solid fa-fire text-danger"></i>'
    elif 98 <= percentage <= 99:
        return '<i class="fa-solid fa-fire text-danger"></i><i class="fa-solid fa-fire text-danger"></i><i class="fa-solid fa-fire text-danger"></i><i class="fa-solid fa-fire text-danger"></i>'
    elif percentage == 100:
        return '<i class="fa-solid fa-fire text-danger"></i><i class="fa-solid fa-fire text-danger"></i><i class="fa-solid fa-fire text-danger"></i><i class="fa-solid fa-fire text-danger"></i><i class="fa-solid fa-fire text-danger"></i> <i class="fa-solid fa-check text-success"></i>'
    
    return ""

