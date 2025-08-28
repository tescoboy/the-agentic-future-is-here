"""
Pagination utilities.
"""

from typing import Dict, Any
from urllib.parse import urlencode


def create_pagination_info(total: int, page: int, page_size: int) -> Dict[str, Any]:
    """Create pagination information."""
    total_pages = (total + page_size - 1) // page_size
    current_page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    # Calculate page range (show up to 7 pages)
    start_page = max(1, current_page - 3)
    end_page = min(total_pages, start_page + 6)
    if end_page - start_page < 6:
        start_page = max(1, end_page - 6)
    
    page_range = list(range(start_page, end_page + 1))
    
    return {
        'total': total,
        'total_pages': total_pages,
        'current_page': current_page,
        'page_size': page_size,
        'page_range': page_range,
        'has_previous': current_page > 1,
        'has_next': current_page < total_pages,
        'previous_page': current_page - 1 if current_page > 1 else None,
        'next_page': current_page + 1 if current_page < total_pages else None,
        'start_index': (current_page - 1) * page_size + 1,
        'end_index': min(current_page * page_size, total)
    }


def build_page_urls(base_url: str, current_params: Dict[str, Any], page: int) -> str:
    """Build URL for a specific page while preserving other query parameters."""
    params = current_params.copy()
    params['page'] = page
    return f"{base_url}?{urlencode(params)}"

