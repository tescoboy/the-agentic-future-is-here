"""
Sales Agent Contract Constants
Repo: reference/salesagent
Commit: 0a0403c
File: examples/upstream_quickstart.py (line 69)
Method: get_products(brief: str, tenant_id: Optional[str] = None, **kwargs)
"""

from typing import Optional, List, Dict, Any
from app.services._contract_utils import get_salesagent_commit

# Method name from reference repository
SALES_METHOD = "rank_products"


def get_default_sales_prompt() -> str:
    """
    Get the default sales prompt.
    
    Updated for all tenants with web grounding integration
    """
    return """You are an expert media seller working for {tenant_name}. your job is find realvent products for a programmatic advertising campaign.
Campaign Brief: {brief}
Available Products:
{products}
helpful live web search results that relate to available products (may not always be provided)
{web_grounding_results}
Your task:
1. Analyze each product's relevance to the campaign brief. Use the product title and description and be sure to use the helpful live web search results that relates to that product.

2. Rank products from most to least relevant. be sure to use the helpful live web search results that relates to that product.
3. Return the top products
Response format (JSON only):
{
  "products": [
    {
      "product_id": "product_id_here",
      "relevance_score": 0.95,
      "reasoning": "Why this product is relevant be sure to use the helpful live web search results that relates to that product.  Answer in as if you are a senioir copy writer at {tenant_name}"
    }
  ]
}
Focus on:
- Targeting alignment with brief requirements
-be sure to use the helpful live web search results that relates to that product. 

VOICE
Always be positive. remember your goal is to get the advertiser to chose your suggest products so make them stand out againt the competi
tion. 

Return ONLY the JSON response, no additional text."""


def build_sales_params(brief: str, tenant_prompt: Optional[str] = None) -> dict:
    """
    Build parameters for sales agent request.
    
    Args:
        brief: The buyer's brief description
        tenant_prompt: Optional tenant-specific prompt override
        web_snippets: Optional list of web context snippets
        
    Returns:
        Dictionary with required parameters for sales agent
        
    Raises:
        ValueError: If brief is empty
    """
    if not brief or not brief.strip():
        raise ValueError("brief cannot be empty")
    
    # Select prompt: tenant override or default
    prompt = tenant_prompt or get_default_sales_prompt()
    
    # Build base parameters
    params = {
        "brief": brief.strip()
    }
    
    return params

