"""
Product RAG Pre-Filter Service
Copied from reference/signals-agent at commit ce1081c
Repository: https://github.com/adcontextprotocol/signals-agent

Implements RAG/FTS/Hybrid search pipeline for filtering buyer briefs against tenant products
before sending top-K candidates to AI ranking.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import Product
from app.utils.embeddings import batch_embed_text, search_similar_products
from app.utils.fts import fts_search_products

logger = logging.getLogger(__name__)

# Default constants copied from signals-agent
DEFAULT_TOP_K = 50
RAG_WEIGHT = 0.7  # 70% RAG + 30% FTS in hybrid mode
EMBEDDING_DIMENSION = 768  # text-embedding-004 produces 768-dim vectors


def choose_search_strategy(brief: str) -> Tuple[str, bool]:
    """
    Choose search strategy based on brief characteristics.
    Copied from signals-agent/main.py determine_search_strategy()
    
    Returns:
        Tuple of (strategy, use_expansion)
        strategy: 'rag', 'fts', or 'hybrid'
        use_expansion: whether to use AI query expansion
    """
    # Check for technical/exact match patterns
    if any(op in brief.upper() for op in [' AND ', ' OR ', ' NOT ', '"', "'"]):
        # Boolean operators indicate FTS is better
        return ('fts', False)
    
    # Check for product IDs or technical codes
    if brief.replace('-', '').replace('_', '').replace('.', '').isalnum() and \
       any(c.isdigit() for c in brief) and len(brief) > 8:
        # Looks like a technical ID
        return ('fts', False)
    
    # Check for company/brand names (usually capitalized, specific)
    words = brief.split()
    capitalized_count = sum(1 for w in words if w and w[0].isupper())
    if capitalized_count >= len(words) * 0.6 and len(words) <= 3:
        # Likely company/brand names
        return ('fts', False)
    
    # Check for behavioral/intent indicators → RAG is best
    intent_indicators = [
        'interested', 'likely', 'intent', 'looking', 'seeking', 'want',
        'lifestyle', 'behavior', 'habit', 'preference', 'affinity',
        'enthusiast', 'lover', 'fan', 'conscious', 'aware', 'minded'
    ]
    if any(indicator in brief.lower() for indicator in intent_indicators):
        return ('rag', True)
    
    # Check for conceptual/thematic queries → RAG is best
    conceptual_terms = [
        'luxury', 'premium', 'budget', 'eco', 'green', 'sustainable',
        'health', 'wellness', 'fitness', 'active', 'affluent', 'trendy',
        'modern', 'traditional', 'conservative', 'progressive'
    ]
    if any(term in brief.lower() for term in conceptual_terms):
        return ('rag', True)
    
    # Check for demographic queries → Hybrid works well
    demographic_terms = [
        'age', 'gender', 'income', 'education', 'parent', 'family',
        'married', 'single', 'retired', 'student', 'professional',
        'homeowner', 'renter', 'urban', 'suburban', 'rural'
    ]
    if any(term in brief.lower() for term in demographic_terms):
        # Hybrid search with expansion for demographic queries
        return ('hybrid', len(words) <= 3)  # Expand if query is short
    
    # Default strategy based on query length
    word_count = len(words)
    
    if word_count == 1:
        # Single word - use RAG with expansion
        return ('rag', True)
    elif word_count == 2:
        # Two words - use hybrid with expansion
        return ('hybrid', True)
    elif word_count <= 4:
        # Medium query - use hybrid, expansion depends on specificity
        has_specific_terms = any(w.lower() in ['with', 'without', 'only', 'not', 'except'] for w in words)
        return ('hybrid', not has_specific_terms)
    else:
        # Long query - use hybrid without expansion
        return ('hybrid', False)


async def expand_query_with_ai(brief: str) -> List[str]:
    """
    Expand query using AI to generate related terms.
    Copied from signals-agent/embeddings.py expand_query()
    
    Args:
        brief: Original search brief
        
    Returns:
        List of expanded search terms
    """
    try:
        import google.generativeai as genai
        from app.utils.env import get_gemini_api_key
        
        api_key = get_gemini_api_key()
        if not api_key:
            print("WARNING: Gemini API key not available, skipping query expansion")
            return [brief]
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Generate 5 related search terms for this advertising brief: "{brief}"
        
        Focus on:
        - Synonyms and related concepts
        - Broader and narrower terms
        - Industry-specific terminology
        
        Return only the terms, separated by commas. Do not include explanations.
        """
        
        response = model.generate_content(prompt)
        expanded_terms = [term.strip() for term in response.text.split(',')]
        
        # Ensure original query is included
        if brief.lower() not in [term.lower() for term in expanded_terms]:
            expanded_terms.insert(0, brief)
        
        return expanded_terms[:6]  # Limit to 6 terms
        
    except Exception as e:
        print(f"WARNING: Query expansion failed: {e}")
        return [brief]  # Fall back to original query


async def semantic_search(session: Session, tenant_id: int, brief: str, limit: int) -> List[Dict[str, Any]]:
    """
    Search products using semantic similarity (RAG).
    
    Args:
        session: Database session
        tenant_id: Tenant ID to filter products
        brief: Search brief
        limit: Maximum number of results
        
    Returns:
        List of product dicts with rag_score
    """
    try:
        # Get query embedding
        query_embedding = await batch_embed_text([brief])
        if not query_embedding:
            return []
        
        # Search similar embeddings
        results = await search_similar_products(session, tenant_id, query_embedding[0], limit)
        
        # Add rag_score to results
        for result in results:
            result['rag_score'] = result.get('similarity_score', 0)
            result['match_reason'] = 'semantic_similarity'
        
        return results
        
    except Exception as e:
        print(f"ERROR: Semantic search failed: {e}")
        return []


async def fts_search(session: Session, tenant_id: int, brief: str, limit: int) -> List[Dict[str, Any]]:
    """
    Search products using full-text search (FTS).
    
    Args:
        session: Database session
        tenant_id: Tenant ID to filter products
        brief: Search brief
        limit: Maximum number of results
        
    Returns:
        List of product dicts with fts_score
    """
    try:
        results = fts_search_products(session, tenant_id, brief, limit)
        
        # Add fts_score to results
        for result in results:
            result['fts_score'] = result.get('relevance_score', 0)
            result['match_reason'] = 'text_match'
        
        return results
        
    except Exception as e:
        print(f"ERROR: FTS search failed: {e}")
        return []


def hybrid_rank(rag_results: List[Dict], fts_results: List[Dict], limit: int) -> List[Dict[str, Any]]:
    """
    Combine RAG and FTS results using hybrid ranking.
    Copied from signals-agent/adapters/liveramp.py search_segments_hybrid()
    
    Args:
        rag_results: RAG search results
        fts_results: FTS search results
        limit: Maximum number of results
        
    Returns:
        List of product dicts with combined_score
    """
    results_map = {}
    
    # Add RAG results
    for result in rag_results:
        product_id = result['product_id']
        results_map[product_id] = result.copy()
        results_map[product_id]['rag_score'] = result.get('rag_score', 0)
        results_map[product_id]['fts_score'] = 0  # Initialize FTS score
        results_map[product_id]['combined_score'] = RAG_WEIGHT * result.get('rag_score', 0)  # RAG-only score
    
    # Normalize FTS scores and combine
    max_relevance = max([abs(r.get('fts_score', 0)) for r in fts_results], default=1)
    
    for result in fts_results:
        product_id = result['product_id']
        
        # Normalize FTS score to 0-1 range
        fts_score = abs(result.get('fts_score', 0)) / max(abs(max_relevance), 1)
        
        if product_id in results_map:
            # Combine scores
            results_map[product_id]['fts_score'] = fts_score
            results_map[product_id]['combined_score'] = (
                RAG_WEIGHT * results_map[product_id]['rag_score'] +
                (1 - RAG_WEIGHT) * fts_score
            )
        else:
            # FTS-only result
            result_copy = result.copy()
            result_copy['fts_score'] = fts_score
            result_copy['rag_score'] = 0
            result_copy['combined_score'] = (1 - RAG_WEIGHT) * fts_score
            results_map[product_id] = result_copy
    
    # Sort by combined score, then by product_id for stability
    results = list(results_map.values())
    results.sort(key=lambda x: (x.get('combined_score', 0), -x.get('product_id', 0)), reverse=True)
    
    return results[:limit]


async def filter_products_for_brief(session: Session, tenant_id: int, brief: str, limit: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
    """
    Filter products for a buyer brief using RAG/FTS/Hybrid search.
    
    Args:
        session: Database session
        tenant_id: Tenant ID to filter products
        brief: Buyer brief text
        limit: Maximum number of results (default: 50)
        
    Returns:
        List of product dicts with {product_id, rag_score, match_reason}
    """
    if not brief or not brief.strip():
        return []
    
    # Choose search strategy
    strategy, use_expansion = choose_search_strategy(brief)
    
    # Expand query if needed
    expanded = False
    if use_expansion:
        try:
            expanded_terms = await expand_query_with_ai(brief)
            if len(expanded_terms) > 1:
                brief = ' '.join(expanded_terms)
                expanded = True
        except Exception as e:
            print(f"WARNING: Query expansion failed: {e}")
    
    results = []
    
    if strategy == 'rag':
        results = await semantic_search(session, tenant_id, brief, limit)
        # Fall back to FTS if semantic search returns no results
        if not results:
            print(f"INFO: Semantic search returned no results, falling back to FTS for: {brief[:50]}...")
            results = await fts_search(session, tenant_id, brief, limit)
        
    elif strategy == 'fts':
        results = await fts_search(session, tenant_id, brief, limit)
        
    elif strategy == 'hybrid':
        # Get both RAG and FTS results
        rag_results = await semantic_search(session, tenant_id, brief, limit * 2)
        fts_results = await fts_search(session, tenant_id, brief, limit * 2)
        
        # Combine using hybrid ranking
        results = hybrid_rank(rag_results, fts_results, limit)
    
    # Log the search strategy used
    print(f"INFO: rag_strategy={strategy} expanded={expanded} candidates={len(results)}")
    
    return results
