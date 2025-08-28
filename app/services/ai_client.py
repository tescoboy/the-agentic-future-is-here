"""
AI ranking client for sales products.
Copied from reference/salesagent/product_catalog_providers/ai.py @ 0a0403c
"""

import json
import os
import asyncio
from typing import List, Dict, Any
import google.generativeai as genai

from app.models import Product
from app.services.sales_contract import get_default_sales_prompt


async def rank_products_with_ai(brief: str, products: List[Product], prompt: str) -> List[Dict[str, Any]]:
    """
    Rank products using Gemini AI.
    
    Args:
        brief: Buyer brief (non-empty)
        products: List of tenant products
        prompt: AI prompt (custom or default)
        
    Returns:
        List of ranked items with product_id, reason, score
        
    Raises:
        RuntimeError: If AI ranking fails (no fallback)
    """
    if not brief or not brief.strip():
        raise RuntimeError("brief cannot be empty")
    
    if not products:
        return []
    
    # Initialize Gemini
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is required for AI product catalog")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        raise RuntimeError(f"AI ranking failed: initialization error - {str(e)}")
    
    # Prepare products data for AI analysis
    products_data = []
    for product in products:
        product_info = {
            "product_id": str(product.id),
            "name": product.name,
            "description": product.description or "",
            "delivery_type": product.delivery_type,
            "price_cpm": product.price_cpm,
        }
        
        # Add formats if available
        if product.formats_json:
            try:
                formats = json.loads(product.formats_json)
                product_info["formats"] = formats
            except (json.JSONDecodeError, TypeError):
                product_info["formats"] = []
        
        # Add targeting if available
        if product.targeting_json:
            try:
                targeting = json.loads(product.targeting_json)
                product_info["targeting"] = targeting
            except (json.JSONDecodeError, TypeError):
                product_info["targeting"] = {}
        
        products_data.append(product_info)
    
    # Create the AI prompt
    ai_prompt = f"""
{prompt}

Campaign Brief: {brief}

Available Products:
{json.dumps(products_data, indent=2)}

Your task:
1. Analyze each product's relevance to the campaign brief
2. Consider targeting capabilities, format compatibility, and pricing
3. Rank products from most to least relevant
4. Return the top products

Response format (JSON only):
{{
  "products": [
    {{
      "product_id": "product_id_here",
      "relevance_score": 0.95,
      "reasoning": "Why this product is relevant"
    }}
  ]
}}

Focus on:
- Targeting alignment with brief requirements
- Format suitability for campaign goals
- Pricing compatibility with budget
- Geographic targeting match
- Delivery type appropriateness

Return ONLY the JSON response, no additional text.
"""
    
    try:
        # Generate AI response (wrap sync call in asyncio.to_thread)
        response = await asyncio.to_thread(
            model.generate_content,
            ai_prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=2048)
        )
        
        # Parse AI response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "")
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "")
        
        response_text = response_text.strip()
        
        ai_result = json.loads(response_text)
        
        # Convert to our contract format
        ranked_items = []
        for product_analysis in ai_result.get("products", []):
            ranked_items.append({
                "product_id": int(product_analysis["product_id"]),
                "reason": product_analysis.get("reasoning", "AI analysis"),
                "score": product_analysis.get("relevance_score", 0.5)
            })
        
        return ranked_items
        
    except json.JSONDecodeError as e:
        raise RuntimeError(f"AI ranking failed: invalid response format - {str(e)}")
    except Exception as e:
        raise RuntimeError(f"AI ranking failed: {str(e)}")
