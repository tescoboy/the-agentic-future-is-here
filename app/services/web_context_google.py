"""
Google Search grounding client for Gemini.
Fetches web context snippets using Gemini API with google_search tool.
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from app.utils.env import get_gemini_api_key

logger = logging.getLogger(__name__)


async def fetch_web_context(brief: str, timeout_ms: int, max_snippets: int, model: str, provider: str, custom_prompt: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Fetch web context snippets using Gemini API.
    
    Args:
        brief: Buyer brief to search for context
        timeout_ms: Timeout in milliseconds
        max_snippets: Maximum number of snippets to return
        model: Gemini model to use
        provider: Tool provider (google_search or google_search_retrieval)
        
    Returns:
        Dict with snippets list and metadata
        
    Raises:
        RuntimeError: For actionable errors (missing API key, quota, auth, timeout, unsupported model)
    """
    if not brief or not brief.strip():
        return {"snippets": [], "metadata": {}}
    
    # Get API key
    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError("web grounding enabled but GEMINI_API_KEY missing")
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Validate model support - simplified for now
        if not model.startswith(('gemini-1.5-', 'gemini-2.0-', 'gemini-2.5-')):
            raise RuntimeError(f"web grounding unsupported for model '{model}'")
        
        # Create model instance with web search capability
        model_instance = genai.GenerativeModel(model)
        
        # Use custom prompt if provided, otherwise use default
        if custom_prompt and context:
            from app.utils.macro_processor import MacroProcessor
            system_prompt = MacroProcessor.process_prompt(custom_prompt, context)
        else:
            # Default web grounding prompt
            tenant_name = context.get('tenant_name', 'Netflix')
            platform_context = context.get('platform_context', 'Netflix platform')
            search_focus = context.get('search_focus', 'generic content')
            system_prompt = f"""You are a consultant working for {tenant_name}. Your task is enriching an advertising campaign brief with fresh, web-sourced context.

IMPORTANT: You are researching content from {platform_context}. Stay focused on {tenant_name} content only.

{context.get('search_boundary', 'Focus only on content from this platform.')}

The sales team thinks the following products may answer the advertisers brief and they need your help researching them so they can recommend them.

Products = {{product_catalog}}

Campaign Brief:
{{brief}}

Instructions:
1. For EACH product, search for SPECIFIC information about that exact title/name.
2. Do NOT search for generic {search_focus} - search for the specific product listed.
3. Extract **unique, factual snippets** (≤350 characters each) that describe:
   - The specific product's target audience, cultural relevance, or themes
   - Recent popularity, awards, chart performance, or positive press coverage
   - Key performers, storylines, or notable events tied to THIS specific product
4. Each snippet must be UNIQUE to the specific product - avoid generic information.
5. Do not invent information. Only include details from real search results.
6. Return plain snippets, no formatting.

Response format:
{{
  "snippets": [
    "Snippet 1 here…",
    "Snippet 2 here…"
  ]
}}"""
        
        # Execute web search with timeout
        try:
            # Use the web search capability
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    model_instance.generate_content,
                    [system_prompt, brief.strip()],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=1000
                    ),
                    safety_settings=[
                        {
                            "category": "HARM_CATEGORY_HARASSMENT",
                            "threshold": "BLOCK_NONE"
                        },
                        {
                            "category": "HARM_CATEGORY_HATE_SPEECH", 
                            "threshold": "BLOCK_NONE"
                        },
                        {
                            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            "threshold": "BLOCK_NONE"
                        },
                        {
                            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                            "threshold": "BLOCK_NONE"
                        }
                    ]
                ),
                timeout=timeout_ms / 1000.0
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"web grounding timeout after {timeout_ms}ms")
        
        # Extract snippets and metadata
        snippets = []
        metadata = {
            "webSearchQueries": [],
            "sources": []
        }
        
        # Check if response has grounding metadata
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            
            # Extract grounding metadata if available
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                grounding_meta = candidate.grounding_metadata
                
                # Extract search queries
                if hasattr(grounding_meta, 'web_search_queries'):
                    metadata["webSearchQueries"] = list(grounding_meta.web_search_queries)
                
                # Extract sources
                if hasattr(grounding_meta, 'grounding_chunks'):
                    for chunk in grounding_meta.grounding_chunks:
                        if hasattr(chunk, 'web'):
                            metadata["sources"].append({
                                "uri": chunk.web.uri,
                                "title": chunk.web.title
                            })
        
        # Check response status and content
        if not response or not hasattr(response, 'text'):
            logger.error(f"Invalid response from Gemini API: {response}")
            raise RuntimeError("web grounding failed: invalid response from API")
        
        # Check if response was blocked or failed
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                if candidate.finish_reason == 2:  # BLOCKED
                    logger.error("Gemini API blocked the request")
                    raise RuntimeError("web grounding failed: request blocked by API")
                elif candidate.finish_reason == 3:  # SAFETY
                    logger.error("Gemini API blocked request due to safety concerns")
                    raise RuntimeError("web grounding failed: request blocked for safety")
        
        # Extract snippets from response text
        response_text = response.text.strip()
        logger.info(f"WEB_DEBUG: Raw response text: {response_text[:200]}...")
        
        # Try to parse as JSON first (common with structured prompts)
        try:
            import json
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove trailing ```
            
            response_text = response_text.strip()
            parsed_json = json.loads(response_text)
            
            if isinstance(parsed_json, dict) and "snippets" in parsed_json:
                # Extract snippets from JSON structure
                json_snippets = parsed_json["snippets"]
                if isinstance(json_snippets, list):
                    for snippet in json_snippets[:max_snippets]:
                        if isinstance(snippet, str) and len(snippet) > 10:
                            # Enforce character limit
                            if len(snippet) > 350:
                                snippet = snippet[:347] + "..."
                            snippets.append(snippet)
                    
                    logger.info(f"WEB_DEBUG: Successfully parsed {len(snippets)} snippets from JSON response")
                    # Skip the plain text parsing below
                    if snippets:
                        # Enforce total character limit
                        total_chars = sum(len(s) for s in snippets)
                        if total_chars > 1000:
                            # Trim snippets to fit within limit
                            trimmed_snippets = []
                            current_total = 0
                            for snippet in snippets:
                                if current_total + len(snippet) <= 1000:
                                    trimmed_snippets.append(snippet)
                                    current_total += len(snippet)
                                else:
                                    break
                            snippets = trimmed_snippets
                        
                        # Remove duplicates
                        seen = set()
                        unique_snippets = []
                        for snippet in snippets:
                            if snippet not in seen:
                                seen.add(snippet)
                                unique_snippets.append(snippet)
                        
                        return {
                            "snippets": unique_snippets,
                            "metadata": metadata
                        }
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.info(f"WEB_DEBUG: Not a valid JSON response, falling back to text parsing: {str(e)}")
            # Continue with plain text parsing below
        
        # Fallback to plain text parsing
        if response_text:
            # Split on bullet points, line breaks, or numbered lists
            lines = re.split(r'[\n•\-\*\d+\.]', response_text)
            lines = [line.strip() for line in lines if line.strip()]
            
            # Clean and filter snippets
            for line in lines[:max_snippets]:
                # Strip HTML tags and extra whitespace
                clean_line = re.sub(r'<[^>]+>', '', line)
                clean_line = re.sub(r'\s+', ' ', clean_line).strip()
                
                if clean_line and len(clean_line) > 10:  # Minimum meaningful length
                    # Enforce character limit
                    if len(clean_line) > 350:
                        clean_line = clean_line[:347] + "..."
                    snippets.append(clean_line)
            
            # If no snippets found with bullet points, try to extract from paragraphs
            if not snippets and len(response_text) > 50:
                # Split into sentences and take first few
                sentences = re.split(r'[.!?]', response_text)
                sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
                
                for sentence in sentences[:max_snippets]:
                    clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
                    if len(clean_sentence) > 20 and len(clean_sentence) <= 350:
                        snippets.append(clean_sentence)
        
        # Enforce total character limit
        total_chars = sum(len(s) for s in snippets)
        if total_chars > 1000:
            # Trim snippets to fit within limit
            trimmed_snippets = []
            current_total = 0
            for snippet in snippets:
                if current_total + len(snippet) <= 1000:
                    trimmed_snippets.append(snippet)
                    current_total += len(snippet)
                else:
                    break
            snippets = trimmed_snippets
        
        # Remove duplicates
        seen = set()
        unique_snippets = []
        for snippet in snippets:
            if snippet not in seen:
                seen.add(snippet)
                unique_snippets.append(snippet)
        
        return {
            "snippets": unique_snippets,
            "metadata": metadata
        }
        
    except RuntimeError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Web grounding error: {str(e)}")
        
        if "quota" in error_msg or "quota exceeded" in error_msg:
            raise RuntimeError("web grounding quota exceeded")
        elif "auth" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg or "api key" in error_msg:
            raise RuntimeError("web grounding authorization failed - check API key")
        elif "malformed" in error_msg or "invalid response" in error_msg:
            raise RuntimeError("web grounding failed: invalid response format")
        elif "timeout" in error_msg:
            raise RuntimeError(f"web grounding timeout after {timeout_ms}ms")
        else:
            # Log the actual error for debugging but don't expose it
            raise RuntimeError(f"web grounding failed: {str(e)[:100]}...")
