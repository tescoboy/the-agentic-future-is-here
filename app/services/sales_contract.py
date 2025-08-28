"""
Sales Agent Contract Constants
Repo: reference/salesagent
Commit: 0a0403c
File: examples/upstream_quickstart.py (line 69)
Method: get_products(brief: str, tenant_id: Optional[str] = None, **kwargs)
"""

from typing import Optional
from app.services._contract_utils import get_salesagent_commit

# Method name from reference repository
SALES_METHOD = "rank_products"


def get_default_sales_prompt() -> str:
    """
    Get the default sales prompt.
    
    Copied from reference/salesagent/product_catalog_providers/ai.py @ 0a0403c
    """
    return """You are an expert media buyer analyzing products for a programmatic advertising campaign.

Campaign Brief: {brief}

Available Products:
{products}

Your task:
1. Analyze each product's relevance to the campaign brief
2. Consider targeting capabilities, format compatibility, and pricing
3. Rank products from most to least relevant
4. Return the top products

Response format (JSON only):
{
  "products": [
    {
      "product_id": "product_id_here",
      "relevance_score": 0.95,
      "reasoning": "Why this product is relevant"
    }
  ]
}

Focus on:
- Targeting alignment with brief requirements
- Format suitability for campaign goals
- Pricing compatibility with budget
- Geographic targeting match
- Delivery type appropriateness

Return ONLY the JSON response, no additional text."""


def build_sales_params(brief: str, tenant_prompt: Optional[str] = None) -> dict:
    """
    Build parameters for sales agent request.
    
    Args:
        brief: The buyer's brief description
        tenant_prompt: Optional tenant-specific prompt override
        
    Returns:
        Dictionary with required parameters for sales agent
        
    Raises:
        ValueError: If brief is empty
    """
    if not brief or not brief.strip():
        raise ValueError("brief cannot be empty")
    
    # Select prompt: tenant override or default
    prompt = tenant_prompt or get_default_sales_prompt()
    
    # Return minimal required structure from reference contract
    # Based on examples/upstream_quickstart.py line 69
    return {
        "brief": brief.strip()
    }

