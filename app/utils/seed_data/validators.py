"""
Validation functions for seed data.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def validate_tenant_data(tenant_data: Dict[str, Any]) -> bool:
    """Validate tenant data from CSV or other sources."""
    required_fields = ['name', 'slug']
    
    for field in required_fields:
        if field not in tenant_data or not tenant_data[field]:
            logger.warning(f"Missing required field: {field}")
            return False
    
    # Validate slug format
    slug = tenant_data['slug']
    if not slug.replace('-', '').replace('_', '').isalnum():
        logger.warning(f"Invalid slug format: {slug}")
        return False
    
    return True


def validate_product_data(product_data: Dict[str, Any]) -> bool:
    """Validate product data from CSV or other sources."""
    required_fields = ['name', 'description', 'price_cpm', 'delivery_type', 'formats', 'targeting_json']
    
    for field in required_fields:
        if field not in product_data:
            logger.warning(f"Missing required field: {field}")
            return False
    
    # Validate price
    try:
        price = float(product_data['price_cpm'])
        if price < 0:
            logger.warning(f"Invalid price: {price}")
            return False
    except (ValueError, TypeError):
        logger.warning(f"Invalid price format: {product_data['price_cpm']}")
        return False
    
    # Validate delivery type
    valid_delivery_types = ['guaranteed', 'non_guaranteed', 'mixed']
    if product_data['delivery_type'] not in valid_delivery_types:
        logger.warning(f"Invalid delivery type: {product_data['delivery_type']}")
        return False
    
    return True
