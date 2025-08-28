"""Results processing utilities for buyer UI."""

from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.repos.products import get_product_by_id
from app.repos.tenants import get_tenant_by_id
from app.repos.external_agents import get_external_agent_by_id


def parse_agent_selections(agents_list: List[str], db_session: Session = None) -> Tuple[List[int], List[Any]]:
    """
    Parse agent selection list into tenant_ids and external_agents.
    
    Args:
        agents_list: List of agent strings like ["sales:tenant:1", "signals:external:2"]
        
    Returns:
        Tuple of (tenant_ids, external_agents)
        
    Raises:
        ValueError: If malformed agent value encountered
    """
    tenant_ids = []
    external_agents = []
    
    for agent_str in agents_list:
        try:
            parts = agent_str.split(":")
            if len(parts) != 3:
                raise ValueError(f"Invalid agent format: {agent_str}")
            
            agent_type, source, agent_id = parts
            
            if agent_type == "sales" and source == "tenant":
                tenant_ids.append(int(agent_id))
            elif agent_type == "signals" and source == "external":
                if db_session:
                    try:
                        external_agent = get_external_agent_by_id(db_session, int(agent_id))
                        if external_agent:
                            external_agents.append(external_agent)
                    except Exception:
                        # Skip invalid external agents
                        pass
            elif agent_type == "sales" and source == "external":
                # Reserve for future external sales support
                if db_session:
                    try:
                        external_agent = get_external_agent_by_id(db_session, int(agent_id))
                        if external_agent and external_agent.agent_type == "sales":
                            external_agents.append(external_agent)
                    except Exception:
                        # Skip invalid external agents
                        pass
            else:
                raise ValueError(f"Unsupported agent type: {agent_str}")
                
        except (ValueError, IndexError) as e:
            raise ValueError(f"Malformed agent value: {agent_str}") from e
    
    return tenant_ids, external_agents


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


def enrich_sales_results(results: List[Dict[str, Any]], db_session: Session) -> List[Dict[str, Any]]:
    """
    Enrich sales results with product data.
    
    Args:
        results: List of sales agent results from orchestrator
        db_session: Database session
        
    Returns:
        Enriched results with product name and description
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
                
                enriched_item = {
                    **item,
                    "product_name": product.name,
                    "product_description": product.description
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
