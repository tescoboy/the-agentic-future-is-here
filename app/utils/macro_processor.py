"""
Macro processor for prompt templates.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class MacroProcessor:
    """Process macros in prompt templates."""
    
    # Available macros
    AVAILABLE_MACROS = {
        "{brief}": "The buyer's campaign brief",
        "{product_catalog}": "The publisher's product catalog",
        "{web_grounding_results}": "Results from web grounding search",
        "{tenant_name}": "The publisher's name",
        "{tenant_slug}": "The publisher's slug"
    }
    
    @classmethod
    def get_available_macros(cls) -> Dict[str, str]:
        """Get list of available macros with descriptions."""
        return cls.AVAILABLE_MACROS.copy()
    
    @classmethod
    def process_prompt(cls, prompt: str, context: Dict[str, Any]) -> str:
        """
        Process a prompt template by replacing macros with actual values.
        
        Args:
            prompt: The prompt template with macros
            context: Dictionary containing values for macros
            
        Returns:
            Processed prompt with macros replaced
        """
        if not prompt:
            return ""
        
        result = prompt
        
        # Replace {brief} macro
        if "{brief}" in result and "brief" in context:
            result = result.replace("{brief}", str(context["brief"]))
        
        # Replace {product_catalog} macro
        if "{product_catalog}" in result and "product_catalog" in context:
            catalog_text = cls._format_product_catalog(context["product_catalog"])
            result = result.replace("{product_catalog}", catalog_text)
        
        # Replace {web_grounding_results} macro
        if "{web_grounding_results}" in result and "web_grounding_results" in context:
            grounding_text = cls._format_web_grounding_results(context["web_grounding_results"])
            result = result.replace("{web_grounding_results}", grounding_text)
        
        # Replace {tenant_name} macro
        if "{tenant_name}" in result and "tenant_name" in context:
            result = result.replace("{tenant_name}", str(context["tenant_name"]))
        
        # Replace {tenant_slug} macro
        if "{tenant_slug}" in result and "tenant_slug" in context:
            result = result.replace("{tenant_slug}", str(context["tenant_slug"]))
        
        return result
    
    @classmethod
    def _format_product_catalog(cls, products: List[Dict[str, Any]]) -> str:
        """Format product catalog for prompt inclusion."""
        if not products:
            return "No products available."
        
        catalog_lines = []
        for product in products:
            line = f"- {product.get('name', 'Unknown')}"
            if product.get('description'):
                line += f": {product['description']}"
            if product.get('price_cpm'):
                line += f" (${product['price_cpm']:.2f} CPM)"
            catalog_lines.append(line)
        
        return "\n".join(catalog_lines)
    
    @classmethod
    def _format_web_grounding_results(cls, results: Dict[str, Any]) -> str:
        """Format web grounding results for prompt inclusion."""
        if not results or not results.get("snippets"):
            return "No web grounding results available."
        
        snippets = results.get("snippets", [])
        if not snippets:
            return "No web grounding insights found."
        
        formatted_snippets = []
        for i, snippet in enumerate(snippets, 1):
            formatted_snippets.append(f"{i}. {snippet}")
        
        return "\n".join(formatted_snippets)
    
    @classmethod
    def validate_prompt(cls, prompt: str) -> Dict[str, Any]:
        """
        Validate a prompt template and return information about used macros.
        
        Args:
            prompt: The prompt template to validate
            
        Returns:
            Dictionary with validation results
        """
        if not prompt:
            return {
                "valid": False,
                "error": "Prompt cannot be empty"
            }
        
        used_macros = []
        for macro in cls.AVAILABLE_MACROS:
            if macro in prompt:
                used_macros.append(macro)
        
        return {
            "valid": True,
            "used_macros": used_macros,
            "available_macros": list(cls.AVAILABLE_MACROS.keys())
        }
