"""
Tests for Product RAG Pipeline.
Copied from reference/signals-agent at commit ce1081c
Repository: https://github.com/adcontextprotocol/signals-agent

Tests RAG/FTS/Hybrid search strategy selection and functionality.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session
from app.services.product_rag import (
    choose_search_strategy, 
    expand_query_with_ai, 
    semantic_search, 
    fts_search, 
    hybrid_rank,
    filter_products_for_brief
)
from app.utils.embeddings import batch_embed_text, query_similar_embeddings
from app.utils.fts import fts_search_products


class TestSearchStrategySelection:
    """Test search strategy selection logic."""
    
    def test_boolean_operators_trigger_fts(self):
        """Test that boolean operators trigger FTS strategy."""
        strategy, expansion = choose_search_strategy("luxury AND premium")
        assert strategy == "fts"
        assert expansion is False
        
        strategy, expansion = choose_search_strategy('"exact phrase"')
        assert strategy == "fts"
        assert expansion is False
        
        strategy, expansion = choose_search_strategy("product OR service")
        assert strategy == "fts"
        assert expansion is False
    
    def test_technical_ids_trigger_fts(self):
        """Test that technical IDs trigger FTS strategy."""
        strategy, expansion = choose_search_strategy("PROD-12345-ABC")
        assert strategy == "fts"
        assert expansion is False
        
        strategy, expansion = choose_search_strategy("123456789")
        assert strategy == "fts"
        assert expansion is False
    
    def test_capitalized_brands_trigger_fts(self):
        """Test that capitalized brand names trigger FTS strategy."""
        strategy, expansion = choose_search_strategy("Nike Adidas")
        assert strategy == "fts"
        assert expansion is False
        
        # Test that 2-word capitalized queries go to hybrid (default for 2 words)
        strategy, expansion = choose_search_strategy("Apple iPhone")
        assert strategy == "hybrid"
        assert expansion is True
        
        # Test that not all capitalized queries trigger FTS
        strategy, expansion = choose_search_strategy("Luxury Car")
        assert strategy == "fts"  # 2 capitalized words out of 2 (100%)
        assert expansion is False
    
    def test_intent_indicators_trigger_rag(self):
        """Test that intent indicators trigger RAG strategy."""
        strategy, expansion = choose_search_strategy("interested in luxury")
        assert strategy == "rag"
        assert expansion is True
        
        strategy, expansion = choose_search_strategy("likely to buy")
        assert strategy == "rag"
        assert expansion is True
        
        strategy, expansion = choose_search_strategy("lifestyle behavior")
        assert strategy == "rag"
        assert expansion is True
    
    def test_conceptual_terms_trigger_rag(self):
        """Test that conceptual terms trigger RAG strategy."""
        strategy, expansion = choose_search_strategy("eco friendly")
        assert strategy == "rag"
        assert expansion is True
        
        strategy, expansion = choose_search_strategy("premium luxury")
        assert strategy == "rag"
        assert expansion is True
        
        strategy, expansion = choose_search_strategy("sustainable green")
        assert strategy == "rag"
        assert expansion is True
    
    def test_demographic_terms_trigger_hybrid(self):
        """Test that demographic terms trigger hybrid strategy."""
        strategy, expansion = choose_search_strategy("age 25-35")
        assert strategy == "hybrid"
        assert expansion is True  # Short query (2 words)
        
        strategy, expansion = choose_search_strategy("parents with children")
        assert strategy == "hybrid"
        assert expansion is True  # 3 words, no specific terms
    
    def test_query_length_strategy_selection(self):
        """Test strategy selection based on query length."""
        # Single word
        strategy, expansion = choose_search_strategy("luxury")
        assert strategy == "rag"
        assert expansion is True
        
        # Two words - but "luxury" is a conceptual term, so RAG
        strategy, expansion = choose_search_strategy("luxury cars")
        assert strategy == "rag"
        assert expansion is True
        
        # Two words without conceptual terms
        strategy, expansion = choose_search_strategy("car buyers")
        assert strategy == "hybrid"
        assert expansion is True
        
        # Three words
        strategy, expansion = choose_search_strategy("car buyers interested")
        assert strategy == "rag"  # "interested" is an intent indicator
        assert expansion is True
        
        # Four words with specific terms
        strategy, expansion = choose_search_strategy("car buyers with high income")
        assert strategy == "hybrid"
        assert expansion is False  # Has specific terms
        
        # Five+ words
        strategy, expansion = choose_search_strategy("car buyers with high income levels")
        assert strategy == "hybrid"
        assert expansion is False


class TestQueryExpansion:
    """Test AI query expansion functionality."""
    
    @patch('app.services.product_rag.genai')
    @patch('app.services.product_rag.get_gemini_api_key')
    async def test_query_expansion_success(self, mock_get_key, mock_genai):
        """Test successful query expansion."""
        mock_get_key.return_value = "test-api-key"
        mock_response = MagicMock()
        mock_response.text = "luxury, premium, high-end, exclusive, upscale, sophisticated"
        mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response
        
        expanded = await expand_query_with_ai("luxury")
        assert len(expanded) == 6
        assert "luxury" in expanded
        assert "premium" in expanded
    
    @patch('app.services.product_rag.get_gemini_api_key')
    async def test_query_expansion_missing_api_key(self, mock_get_key):
        """Test query expansion fails with missing API key."""
        mock_get_key.return_value = None
        
        with pytest.raises(ValueError, match="Gemini API key is required for query expansion"):
            await expand_query_with_ai("luxury")
    
    @patch('app.services.product_rag.genai')
    @patch('app.services.product_rag.get_gemini_api_key')
    async def test_query_expansion_fallback(self, mock_get_key, mock_genai):
        """Test query expansion falls back to original query on error."""
        mock_get_key.return_value = "test-api-key"
        mock_genai.GenerativeModel.side_effect = Exception("API error")
        
        expanded = await expand_query_with_ai("luxury")
        assert expanded == ["luxury"]


class TestSemanticSearch:
    """Test semantic search functionality."""
    
    @patch('app.services.product_rag.query_similar_embeddings')
    @patch('app.services.product_rag.batch_embed_text')
    async def test_semantic_search_success(self, mock_batch_embed, mock_query_similar):
        """Test successful semantic search."""
        mock_session = MagicMock(spec=Session)
        
        # Mock embedding generation
        mock_batch_embed.return_value = [[0.1, 0.2, 0.3] * 256]  # 768-dim vector
        
        # Mock similarity search results
        mock_query_similar.return_value = [
            {
                'product_id': 1,
                'name': 'Luxury Car',
                'description': 'Premium vehicle',
                'similarity_score': 0.85
            }
        ]
        
        results = await semantic_search(mock_session, 1, "luxury car", 10)
        
        assert len(results) == 1
        assert results[0]['product_id'] == 1
        assert results[0]['rag_score'] == 0.85
        assert results[0]['match_reason'] == 'semantic_similarity'
    
    @patch('app.services.product_rag.batch_embed_text')
    async def test_semantic_search_no_embeddings(self, mock_batch_embed):
        """Test semantic search with no embeddings generated."""
        mock_session = MagicMock(spec=Session)
        mock_batch_embed.return_value = []
        
        results = await semantic_search(mock_session, 1, "luxury car", 10)
        assert results == []


class TestFTSSearch:
    """Test FTS search functionality."""
    
    @patch('app.utils.fts.fts_search_products')
    async def test_fts_search_success(self, mock_fts_search):
        """Test successful FTS search."""
        mock_session = MagicMock(spec=Session)
        
        # Mock FTS search results
        mock_fts_search.return_value = [
            {
                'product_id': 1,
                'name': 'Luxury Car',
                'description': 'Premium vehicle',
                'relevance_score': 0.9
            }
        ]
        
        results = await fts_search(mock_session, 1, "luxury car", 10)
        
        assert len(results) == 1
        assert results[0]['product_id'] == 1
        assert results[0]['fts_score'] == 0.9
        assert results[0]['match_reason'] == 'text_match'


class TestHybridRanking:
    """Test hybrid ranking functionality."""
    
    def test_hybrid_rank_combines_scores(self):
        """Test that hybrid ranking combines RAG and FTS scores."""
        rag_results = [
            {'product_id': 1, 'rag_score': 0.8, 'name': 'Product 1'},
            {'product_id': 2, 'rag_score': 0.6, 'name': 'Product 2'}
        ]
        
        fts_results = [
            {'product_id': 1, 'fts_score': 0.9, 'name': 'Product 1'},
            {'product_id': 3, 'fts_score': 0.7, 'name': 'Product 3'}
        ]
        
        results = hybrid_rank(rag_results, fts_results, 10)
        
        assert len(results) == 3
        
        # Product 1 should have combined score
        product_1 = next(r for r in results if r['product_id'] == 1)
        expected_score = 0.7 * 0.8 + 0.3 * 0.9  # RAG weight * rag_score + FTS weight * fts_score
        assert abs(product_1['combined_score'] - expected_score) < 0.01
        
        # Product 2 should have RAG-only score
        product_2 = next(r for r in results if r['product_id'] == 2)
        assert product_2['fts_score'] == 0
        assert product_2['combined_score'] == 0.7 * 0.6  # RAG weight * rag_score
        
        # Product 3 should have FTS-only score
        product_3 = next(r for r in results if r['product_id'] == 3)
        assert product_3['rag_score'] == 0
        assert abs(product_3['combined_score'] - (0.3 * 0.7)) < 0.01  # FTS weight * fts_score
    
    def test_hybrid_rank_stable_sorting(self):
        """Test that hybrid ranking uses stable sorting."""
        rag_results = [
            {'product_id': 1, 'rag_score': 0.8, 'name': 'Product 1'},
            {'product_id': 2, 'rag_score': 0.8, 'name': 'Product 2'}  # Same score
        ]
        
        fts_results = [
            {'product_id': 1, 'fts_score': 0.9, 'name': 'Product 1'},
            {'product_id': 2, 'fts_score': 0.9, 'name': 'Product 2'}  # Same score
        ]
        
        results = hybrid_rank(rag_results, fts_results, 10)
        
        # Should maintain order based on product_id for stability
        assert results[0]['product_id'] == 1
        assert results[1]['product_id'] == 2


class TestFilterProductsForBrief:
    """Test the main filter_products_for_brief function."""
    
    @patch('app.services.product_rag.semantic_search')
    @patch('app.services.product_rag.choose_search_strategy')
    async def test_filter_products_rag_strategy(self, mock_choose_strategy, mock_semantic_search):
        """Test filtering with RAG strategy."""
        mock_session = MagicMock(spec=Session)
        mock_choose_strategy.return_value = ('rag', True)
        mock_semantic_search.return_value = [
            {'product_id': 1, 'rag_score': 0.8, 'match_reason': 'semantic_similarity'}
        ]
        
        results = await filter_products_for_brief(mock_session, 1, "luxury car", 10)
        
        assert len(results) == 1
        assert results[0]['product_id'] == 1
        mock_semantic_search.assert_called_once_with(mock_session, 1, "luxury car", 10)
    
    @patch('app.services.product_rag.fts_search')
    @patch('app.services.product_rag.choose_search_strategy')
    async def test_filter_products_fts_strategy(self, mock_choose_strategy, mock_fts_search):
        """Test filtering with FTS strategy."""
        mock_session = MagicMock(spec=Session)
        mock_choose_strategy.return_value = ('fts', False)
        mock_fts_search.return_value = [
            {'product_id': 1, 'fts_score': 0.9, 'match_reason': 'text_match'}
        ]
        
        results = await filter_products_for_brief(mock_session, 1, "luxury car", 10)
        
        assert len(results) == 1
        assert results[0]['product_id'] == 1
        mock_fts_search.assert_called_once_with(mock_session, 1, "luxury car", 10)
    
    @patch('app.services.product_rag.hybrid_rank')
    @patch('app.services.product_rag.fts_search')
    @patch('app.services.product_rag.semantic_search')
    @patch('app.services.product_rag.choose_search_strategy')
    async def test_filter_products_hybrid_strategy(self, mock_choose_strategy, mock_semantic_search, mock_fts_search, mock_hybrid_rank):
        """Test filtering with hybrid strategy."""
        mock_session = MagicMock(spec=Session)
        mock_choose_strategy.return_value = ('hybrid', False)
        mock_semantic_search.return_value = [
            {'product_id': 1, 'rag_score': 0.8, 'match_reason': 'semantic_similarity'}
        ]
        mock_fts_search.return_value = [
            {'product_id': 1, 'fts_score': 0.9, 'match_reason': 'text_match'}
        ]
        mock_hybrid_rank.return_value = [
            {'product_id': 1, 'combined_score': 0.85, 'rag_score': 0.8, 'fts_score': 0.9}
        ]
        
        results = await filter_products_for_brief(mock_session, 1, "luxury car", 10)
        
        assert len(results) == 1
        assert results[0]['product_id'] == 1
        mock_semantic_search.assert_called_once_with(mock_session, 1, "luxury car", 20)  # limit * 2
        mock_fts_search.assert_called_once_with(mock_session, 1, "luxury car", 20)  # limit * 2
        mock_hybrid_rank.assert_called_once()
    
    async def test_filter_products_empty_brief(self):
        """Test filtering with empty brief returns empty results."""
        mock_session = MagicMock(spec=Session)
        
        results = await filter_products_for_brief(mock_session, 1, "", 10)
        assert results == []
        
        results = await filter_products_for_brief(mock_session, 1, "   ", 10)
        assert results == []
    
    @patch('app.services.product_rag.expand_query_with_ai')
    @patch('app.services.product_rag.semantic_search')
    @patch('app.services.product_rag.choose_search_strategy')
    async def test_filter_products_with_expansion(self, mock_choose_strategy, mock_semantic_search, mock_expand):
        """Test filtering with query expansion."""
        mock_session = MagicMock(spec=Session)
        mock_choose_strategy.return_value = ('rag', True)
        mock_expand.return_value = ["luxury", "premium", "high-end"]
        mock_semantic_search.return_value = [
            {'product_id': 1, 'rag_score': 0.8, 'match_reason': 'semantic_similarity'}
        ]
        
        results = await filter_products_for_brief(mock_session, 1, "luxury", 10)
        
        assert len(results) == 1
        mock_expand.assert_called_once_with("luxury")
        mock_semantic_search.assert_called_once_with(mock_session, 1, "luxury premium high-end", 10)
