"""
Tests for AI ranking integration.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.ai_client import rank_products_with_ai
from app.models import Product


@pytest.fixture
def sample_products():
    """Sample products for testing."""
    return [
        Product(
            id=1,
            name="Netflix Sports Stories",
            description="Sports content for advertising",
            delivery_type="guaranteed",
            price_cpm=45.0,
            tenant_id=1,
            formats_json='["video", "ctv"]',
            targeting_json='{"geo": ["US"]}'
        ),
        Product(
            id=2,
            name="Netflix Romance Stories",
            description="Romance content for advertising",
            delivery_type="guaranteed",
            price_cpm=35.0,
            tenant_id=1,
            formats_json='["video", "ctv"]',
            targeting_json='{"geo": ["US"]}'
        )
    ]


@pytest.mark.asyncio
async def test_missing_api_key():
    """Test missing GEMINI_API_KEY raises correct error."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY environment variable is required for AI product catalog"):
            await rank_products_with_ai("sports", [Product(id=1, name="test", tenant_id=1)], "test prompt")


@pytest.mark.asyncio
async def test_empty_brief():
    """Test empty brief raises correct error."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        with pytest.raises(RuntimeError, match="brief cannot be empty"):
            await rank_products_with_ai("", [], "test prompt")
        
        with pytest.raises(RuntimeError, match="brief cannot be empty"):
            await rank_products_with_ai("   ", [], "test prompt")


@pytest.mark.asyncio
async def test_empty_products():
    """Test empty products list returns empty result."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        result = await rank_products_with_ai("sports", [], "test prompt")
        assert result == []


@pytest.mark.asyncio
async def test_valid_ai_ranking(sample_products):
    """Test valid AI ranking returns correct format."""
    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.text = '''
    {
      "products": [
        {
          "product_id": "1",
          "relevance_score": 0.85,
          "reasoning": "Perfect match for sports content"
        },
        {
          "product_id": "2", 
          "relevance_score": 0.45,
          "reasoning": "Limited relevance to sports"
        }
      ]
    }
    '''
    
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            result = await rank_products_with_ai("sports", sample_products, "test prompt")
            
            # Verify result format
            assert len(result) == 2
            assert result[0]["product_id"] == 1
            assert result[0]["score"] == 0.85
            assert result[0]["reason"] == "Perfect match for sports content"
            assert result[1]["product_id"] == 2
            assert result[1]["score"] == 0.45
            assert result[1]["reason"] == "Limited relevance to sports"


@pytest.mark.asyncio
async def test_malformed_ai_response(sample_products):
    """Test malformed AI response raises actionable error."""
    # Mock invalid JSON response
    mock_response = MagicMock()
    mock_response.text = "invalid json response"
    
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            with pytest.raises(RuntimeError, match="AI ranking failed: invalid response format"):
                await rank_products_with_ai("sports", sample_products, "test prompt")


@pytest.mark.asyncio
async def test_ai_response_missing_fields(sample_products):
    """Test AI response with missing fields uses defaults."""
    # Mock response with missing fields
    mock_response = MagicMock()
    mock_response.text = '''
    {
      "products": [
        {
          "product_id": "1"
        }
      ]
    }
    '''
    
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            result = await rank_products_with_ai("sports", sample_products, "test prompt")
            
            # Verify defaults are used
            assert len(result) == 1
            assert result[0]["product_id"] == 1
            assert result[0]["reason"] == "AI analysis"
            assert result[0]["score"] == 0.5


@pytest.mark.asyncio
async def test_tenant_custom_prompt_override(sample_products):
    """Test that tenant custom prompt is used when available."""
    custom_prompt = "Custom tenant prompt for ranking"
    
    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.text = '''
    {
      "products": [
        {
          "product_id": "1",
          "relevance_score": 0.9,
          "reasoning": "Custom analysis"
        }
      ]
    }
    '''
    
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            result = await rank_products_with_ai("sports", sample_products, custom_prompt)
            
            # Verify custom prompt was used
            mock_instance.generate_content.assert_called_once()
            call_args = mock_instance.generate_content.call_args[0][0]
            assert custom_prompt in call_args


@pytest.mark.asyncio
async def test_product_data_formatting(sample_products):
    """Test that product data is formatted correctly for AI."""
    # Mock Gemini response
    mock_response = MagicMock()
    mock_response.text = '{"products": []}'
    
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance
            
            await rank_products_with_ai("sports", sample_products, "test prompt")
            
            # Verify product data format
            call_args = mock_instance.generate_content.call_args[0][0]
            assert '"product_id": "1"' in call_args
            assert '"name": "Netflix Sports Stories"' in call_args
            assert '"description": "Sports content for advertising"' in call_args
            assert '"delivery_type": "guaranteed"' in call_args
            assert '"price_cpm": 45.0' in call_args
            # Check for formats array (JSON formatting may vary)
            assert '"formats"' in call_args
            assert '"video"' in call_args
            assert '"ctv"' in call_args
            # Check for targeting object
            assert '"targeting"' in call_args
            assert '"geo"' in call_args


@pytest.mark.asyncio
async def test_gemini_initialization_error():
    """Test Gemini initialization error raises actionable error."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_key"}):
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_model.side_effect = Exception("Gemini config error")
            
            with pytest.raises(RuntimeError, match="AI ranking failed: initialization error"):
                await rank_products_with_ai("sports", [Product(id=1, name="test", tenant_id=1)], "test prompt")

