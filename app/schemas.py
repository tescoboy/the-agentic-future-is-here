"""
Pydantic schemas for form validation.
"""

from typing import List, Optional
from pydantic import BaseModel, validator
import re


class TenantForm(BaseModel):
    name: str
    slug: str
    
    @validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v


class ProductForm(BaseModel):
    tenant_id: int
    name: str
    description: Optional[str] = None
    price_cpm: float
    delivery_type: str
    formats_json: str = "{}"
    targeting_json: str = "{}"
    
    @validator('price_cpm')
    def validate_price(cls, v):
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v


class BulkDeleteForm(BaseModel):
    product_ids: List[int]

