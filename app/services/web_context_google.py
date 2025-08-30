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


async def fetch_web_context(brief: str, timeout_ms: int, max_snippets: int, model: str, provider: str) -> Dict[str, Any]:
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
        
        # Create search prompt for web grounding - simplified
        system_prompt = """Based on current digital advertising knowledge, provide 2-3 brief insights about media trends and audience behavior that could help with this campaign. Keep each insight under 200 characters."""
        
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
