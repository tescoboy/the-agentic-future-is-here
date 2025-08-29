"""Results enrichment utilities."""

from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.repos.products import get_product_by_id


def enrich_sales_results(results: List[Dict[str, Any]], db_session: Session) -> List[Dict[str, Any]]:
    """
    Enrich sales results with product data.
    
    Args:
        results: List of sales agent results from orchestrator
        db_session: Database session
        
    Returns:
        Enriched results with product name, description, and metadata
    """
    enriched_results = []
    
    for result in results:
        if not result.get("ok") or not result.get("items"):
            enriched_results.append(result)
            continue
        
        enriched_items = []
        warnings = []
        
        for item in result["items"]:
            product_id = item.get("product_id")
            if not product_id:
                continue
                
            try:
                product = get_product_by_id(db_session, product_id)
                if not product:
                    warnings.append(f"Product {product_id} not found")
                    continue
                
                # Parse JSON fields
                formats = []
                targeting = {}
                try:
                    if product.formats_json:
                        import json
                        formats = json.loads(product.formats_json)
                except (json.JSONDecodeError, TypeError):
                    formats = []
                
                try:
                    if product.targeting_json:
                        import json
                        targeting = json.loads(product.targeting_json)
                except (json.JSONDecodeError, TypeError):
                    targeting = {}
                
                enriched_item = {
                    **item,
                    "product_name": product.name,
                    "product_description": product.description,
                    "price_cpm": product.price_cpm,
                    "delivery_type": product.delivery_type,
                    "formats": formats,
                    "targeting": targeting,
                    "is_guaranteed": product.delivery_type.lower() == "guaranteed"
                }
            except Exception as e:
                warnings.append(f"Error fetching product {product_id}: {str(e)}")
                continue
            enriched_items.append(enriched_item)
        
        enriched_result = {
            **result,
            "items": enriched_items
        }
        
        if warnings:
            if "warnings" not in enriched_result:
                enriched_result["warnings"] = []
            enriched_result["warnings"].extend(warnings)
        
        enriched_results.append(enriched_result)
    
    return enriched_results


def calculate_summary_stats(results: List[Dict[str, Any]], signals: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate summary statistics for results.
    
    Args:
        results: Sales agent results
        signals: Signals agent results
        
    Returns:
        Dictionary with success and failure counts
    """
    all_agents = results + signals
    
    success_count = sum(1 for agent in all_agents if agent.get("ok"))
    failure_count = sum(1 for agent in all_agents if not agent.get("ok"))
    
    return {
        "success": success_count,
        "failure": failure_count,
        "total": len(all_agents)
    }

