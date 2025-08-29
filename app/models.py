"""
SQLModel definitions for AdCP Demo entities.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class Tenant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    slug: str = Field(max_length=255, unique=True, index=True)
    custom_prompt: Optional[str] = Field(default=None)
    enable_web_context: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    products: list["Product"] = Relationship(back_populates="tenant")


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: int = Field(foreign_key="tenant.id")
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    price_cpm: float = Field(ge=0.0)
    delivery_type: str = Field(max_length=100)
    formats_json: Optional[str] = Field(default=None)
    targeting_json: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    tenant: Optional[Tenant] = Relationship(back_populates="products")


class ExternalAgent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    base_url: str = Field(max_length=500)
    enabled: bool = Field(default=True)
    agent_type: str = Field(max_length=50, default="sales")
    protocol: str = Field(max_length=10, default="rest")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Rebuild models to ensure relationships are properly set up
Tenant.model_rebuild()
Product.model_rebuild()
ExternalAgent.model_rebuild()

