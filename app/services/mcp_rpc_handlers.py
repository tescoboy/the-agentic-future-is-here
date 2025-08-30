"""MCP JSON-RPC method dispatcher and handlers."""

import logging
from typing import Dict, Any, List, Optional
from sqlmodel import Session

from app.repos.tenants import get_tenant_by_slug
from app.repos.products import list_products
from app.services.ai_client import rank_products_with_ai
from app.services.sales_contract import get_default_sales_prompt
from app.services.product_rag import filter_products_for_brief

logger = logging.getLogger(__name__)


class MCPRPCError(Exception):
    """JSON-RPC error with code and message."""
    
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


async def dispatch(method: str, params: dict, tenant_slug: str, db_session: Session) -> dict:
    """Dispatch JSON-RPC method calls."""
    try:
        if method == "initialize":
            return _initialize(params)
        elif method == "notifications/initialized":
            return _notifications_initialized()
        elif method == "get_products":
            return _get_products(tenant_slug, params, db_session)
        elif method == "rank_products":
            return await _rank_products(tenant_slug, params, db_session)
        elif method == "mcp.get_info":
            return _get_info()
        else:
            raise MCPRPCError(-32601, f"method not found: {method}")
    except MCPRPCError:
        raise
    except Exception as e:
        logger.error(f"Internal error in {method}: {str(e)}")
        raise MCPRPCError(-32000, "internal server error")


def _initialize(params: dict) -> dict:
    """Handle initialize method."""
    # Return minimal JSON-RPC result for initialize
    return {
        "capabilities": {
            "get_products": {},
            "rank_products": {}
        }
    }


def _notifications_initialized() -> dict:
    """Handle notifications/initialized as no-op."""
    # Return empty result for notification
    return {}


def _get_products(tenant_slug: str, params: dict, db_session: Session) -> dict:
    """Handle get_products method."""
    # Validate tenant exists
    tenant = get_tenant_by_slug(db_session, tenant_slug)
    if not tenant:
        raise MCPRPCError(-32602, f"tenant '{tenant_slug}' not found")
    
    # Get tenant's products
    products, _ = list_products(db_session, tenant_id=tenant.id)
    
    # Convert products to AdCP format
    formatted_products = []
    for product in products:
        formatted_product = {
            "product_id": str(product.id),
            "name": product.name,
            "description": product.description or "",
            "delivery_type": product.delivery_type,
            "price_cpm": product.price_cpm,
        }
        
        # Add formats if available
        if product.formats_json:
            try:
                import json
                formats = json.loads(product.formats_json)
                formatted_product["formats"] = formats
            except (json.JSONDecodeError, TypeError):
                formatted_product["formats"] = []
        
        # Add targeting if available
        if product.targeting_json:
            try:
                import json
                targeting = json.loads(product.targeting_json)
                formatted_product["targeting"] = targeting
            except (json.JSONDecodeError, TypeError):
                formatted_product["targeting"] = {}
        
        formatted_products.append(formatted_product)
    
    return {"products": formatted_products}


async def _rank_products(tenant_slug: str, params: dict, db_session: Session) -> dict:
    """Handle rank_products method with RAG pre-filter + AI ranking."""
    # Validate tenant exists
    tenant = get_tenant_by_slug(db_session, tenant_slug)
    if not tenant:
        raise MCPRPCError(-32602, f"tenant '{tenant_slug}' not found")
    
    # Validate brief parameter
    brief = params.get("brief")
    if not brief or not isinstance(brief, str) or not brief.strip():
        raise MCPRPCError(-32602, "brief must be a non-empty string")
    
    # Extract web snippets if provided
    web_snippets = params.get("web_snippets")
    if web_snippets is not None:
        if not isinstance(web_snippets, list):
            raise MCPRPCError(-32602, "web_snippets must be a list of strings")
        for snippet in web_snippets:
            if not isinstance(snippet, str):
                raise MCPRPCError(-32602, "web_snippets must be a list of strings")
    
    try:
        # Step 1: RAG pre-filter to get candidate products
        rag_candidates = await filter_products_for_brief(db_session, tenant.id, brief.strip())
        
        if not rag_candidates:
            # No candidates found, return empty results
            logger.info(f"RAG pre-filter returned no candidates for brief: {brief[:50]}...")
            return {"items": []}
        
        # Step 2: Get full product objects for AI ranking
        candidate_product_ids = [c['product_id'] for c in rag_candidates]
        # Get all products for the tenant (no limit) to ensure we find all candidates
        products, _ = list_products(db_session, tenant_id=tenant.id, limit=1000)
        
        # Filter products to only include RAG candidates
        candidate_products = [p for p in products if p.id in candidate_product_ids]
        
        # Limit to top 50 products to prevent timeout and high token usage
        if len(candidate_products) > 50:
            logger.info(f"Limiting RAG candidates from {len(candidate_products)} to top 50 products to prevent timeout")
            candidate_products = candidate_products[:50]
        
        if not candidate_products:
            # No products found for candidates, return empty results
            logger.warning(f"No products found for RAG candidates: {candidate_product_ids}")
            return {"items": []}
        
        # Step 3: Web grounding per product (if enabled) - now with access to RAG-filtered products
        web_snippets = None
        web_grounding_results = None
        
        if hasattr(tenant, 'enable_web_context') and tenant.enable_web_context:
            try:
                from app.utils.env import get_web_grounding_config
                from app.services.web_context_google import fetch_web_context
                
                web_config = get_web_grounding_config()
                if web_config and web_config.get("enabled", False):
                    logger.info(f"WEB_DEBUG: Performing web grounding per product for tenant {tenant.slug} with {len(candidate_products)} RAG-filtered products")
                    
                    # Generate web grounding snippets per product
                    all_snippets = []
                    product_snippets = {}
                    
                    logger.info(f"WEB_DEBUG: Starting web grounding for {len(candidate_products)} products")
                    
                    for i, product in enumerate(candidate_products, 1):
                        logger.info(f"WEB_DEBUG: Processing product {i}/{len(candidate_products)}: {product.name}")
                        # Prepare context for this specific product
                        context = {
                            "brief": brief,
                            "tenant_name": tenant.name,
                            "tenant_slug": tenant.slug,
                            "product_catalog": [
                                {
                                    "name": product.name,
                                    "description": product.description,
                                    "price_cpm": product.price_cpm,
                                    "delivery_type": product.delivery_type
                                }
                            ]
                        }
                        
                        try:
                            # Get web grounding for this specific product
                            result = await fetch_web_context(
                                brief, 
                                web_config["timeout_ms"], 
                                1,  # 1 snippet per product
                                web_config["model"],
                                web_config["provider"],
                                custom_prompt=getattr(tenant, 'web_grounding_prompt', None),
                                context=context
                            )
                            
                            if result["snippets"]:
                                snippet = result["snippets"][0]  # Take the first snippet
                                all_snippets.append(snippet)
                                product_snippets[product.id] = snippet
                                logger.info(f"WEB_DEBUG: Product {product.name} snippet: {snippet}")
                            else:
                                logger.info(f"WEB_DEBUG: No snippet generated for product {product.name}")
                                
                        except Exception as e:
                            logger.warning(f"WEB_DEBUG: Web grounding failed for product {product.name}: {str(e)}")
                    
                    web_snippets = all_snippets
                    web_grounding_results = {
                        "snippets": all_snippets,
                        "product_snippets": product_snippets,
                        "metadata": {"per_product": True}
                    }
                    
                    logger.info(f"WEB_DEBUG: Web grounding per product successful, got {len(web_snippets)} snippets for {len(product_snippets)} products")
                    
            except Exception as e:
                logger.warning(f"WEB_DEBUG: Web grounding per product failed for tenant {tenant.slug}: {str(e)}")
                web_snippets = None
                web_grounding_results = None
        
        # Step 4: Resolve prompt: tenant custom prompt or default
        prompt = tenant.custom_prompt if tenant.custom_prompt else get_default_sales_prompt()
        prompt_source = "custom" if tenant.custom_prompt else "default"
        
        # Step 5: Call AI ranking on filtered candidates with web grounding results
        try:
            ranked_items = await rank_products_with_ai(brief.strip(), candidate_products, prompt, web_snippets, web_grounding_results)
            
            # Log prompt source (not content)
            logger.info(f"AI ranking completed: prompt_source={prompt_source}, items={len(ranked_items)}")
            
            return {"items": ranked_items}
            
        except RuntimeError as e:
            # If AI ranking fails, fall back to RAG pre-filter results
            error_msg = str(e)
            if "GEMINI_API_KEY" in error_msg:
                logger.warning("AI ranking failed due to missing API key, falling back to RAG pre-filter results")
                
                # Convert RAG candidates to the expected format
                fallback_items = []
                for candidate in rag_candidates[:10]:  # Limit to top 10
                    fallback_items.append({
                        "product_id": str(candidate['product_id']),
                        "relevance_score": candidate.get('rag_score', candidate.get('fts_score', 0.5)),
                        "reasoning": f"RAG pre-filter match: {candidate.get('match_reason', 'semantic_similarity')}"
                    })
                
                return {"items": fallback_items}
            else:
                # Re-raise other RuntimeErrors
                raise
        
    except RuntimeError as e:
        # Map AI errors to JSON-RPC errors
        error_msg = str(e)
        if "GEMINI_API_KEY" in error_msg:
            raise MCPRPCError(-32000, "AI ranking not configured: GEMINI_API_KEY environment variable is required")
        elif "brief cannot be empty" in error_msg:
            raise MCPRPCError(-32602, "brief must be a non-empty string")
        else:
            raise MCPRPCError(-32000, f"AI ranking failed: {error_msg}")
    except Exception as e:
        # Map RAG errors to JSON-RPC errors
        error_msg = str(e)
        if "GEMINI API key is required" in error_msg:
            raise MCPRPCError(-32000, "RAG pre-filter not configured: GEMINI_API_KEY environment variable is required")
        else:
            raise MCPRPCError(-32000, f"RAG pre-filter failed: {error_msg}")


def _get_info() -> dict:
    """Handle mcp.get_info method."""
    return {
        "service": "adcp-sales",
        "version": "0.1.0",
        "capabilities": ["get_products", "rank_products"]
    }


def validate_json_rpc_envelope(data: dict) -> None:
    """Validate JSON-RPC 2.0 envelope structure."""
    if not isinstance(data, dict):
        raise MCPRPCError(-32600, "invalid request: not a JSON object")
    
    if data.get("jsonrpc") != "2.0":
        raise MCPRPCError(-32600, "invalid request: jsonrpc must be '2.0'")
    
    if "id" not in data:
        raise MCPRPCError(-32600, "invalid request: missing id")
    
    if "method" not in data:
        raise MCPRPCError(-32600, "invalid request: missing method")
    
    if not isinstance(data["method"], str):
        raise MCPRPCError(-32600, "invalid request: method must be a string")
    
    if "params" not in data:
        raise MCPRPCError(-32600, "invalid request: missing params")
    
    if not isinstance(data["params"], dict):
        raise MCPRPCError(-32600, "invalid request: params must be an object")

