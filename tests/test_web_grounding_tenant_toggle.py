"""Tests for web grounding tenant toggle functionality."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models import Tenant
from app.utils.env import get_web_grounding_config
from app.services.web_context_google import fetch_web_context

client = TestClient(app)


@pytest.fixture
def sample_tenant():
    """Sample tenant for testing."""
    return Tenant(
        id=1,
        name="Test Publisher",
        slug="test-publisher",
        enable_web_context=False
    )


@pytest.fixture
def sample_tenant_with_web_context():
    """Sample tenant with web context enabled."""
    return Tenant(
        id=1,
        name="Test Publisher",
        slug="test-publisher",
        enable_web_context=True
    )


class TestWebGroundingConfig:
    """Test web grounding configuration."""
    
    @patch.dict('os.environ', {
        'ENABLE_WEB_CONTEXT': '0',
        'WEB_CONTEXT_TIMEOUT_MS': '2000',
        'WEB_CONTEXT_MAX_SNIPPETS': '3',
        'GEMINI_MODEL': 'gemini-2.5-flash'
    })
    def test_web_grounding_config_disabled(self):
        """Test web grounding config when disabled."""
        config = get_web_grounding_config()
        assert config["enabled"] is False
        assert config["timeout_ms"] == 2000
        assert config["max_snippets"] == 3
        assert config["model"] == "gemini-2.5-flash"
        assert config["provider"] == "google_search"
    
    @patch.dict('os.environ', {
        'ENABLE_WEB_CONTEXT': '1',
        'WEB_CONTEXT_TIMEOUT_MS': '3000',
        'WEB_CONTEXT_MAX_SNIPPETS': '5',
        'GEMINI_MODEL': 'gemini-1.5-flash'
    })
    def test_web_grounding_config_enabled(self):
        """Test web grounding config when enabled."""
        config = get_web_grounding_config()
        assert config["enabled"] is True
        assert config["timeout_ms"] == 3000
        assert config["max_snippets"] == 5
        assert config["model"] == "gemini-1.5-flash"
        assert config["provider"] == "google_search_retrieval"
    
    @patch.dict('os.environ', {
        'ENABLE_WEB_CONTEXT': 'invalid',
        'WEB_CONTEXT_TIMEOUT_MS': '2000',
        'WEB_CONTEXT_MAX_SNIPPETS': '3'
    })
    def test_web_grounding_config_invalid_enabled(self):
        """Test web grounding config with invalid enabled value."""
        with pytest.raises(ValueError, match="ENABLE_WEB_CONTEXT must be"):
            get_web_grounding_config()
    
    @patch.dict('os.environ', {
        'ENABLE_WEB_CONTEXT': '1',
        'WEB_CONTEXT_TIMEOUT_MS': 'invalid',
        'WEB_CONTEXT_MAX_SNIPPETS': '3'
    })
    def test_web_grounding_config_invalid_timeout(self):
        """Test web grounding config with invalid timeout."""
        with pytest.raises(ValueError, match="WEB_CONTEXT_TIMEOUT_MS must be"):
            get_web_grounding_config()


class TestWebContextGoogle:
    """Test web context Google service."""
    
    @patch('app.services.web_context_google.get_gemini_api_key')
    @patch('app.services.web_context_google.genai')
    async def test_fetch_web_context_success(self, mock_genai, mock_get_api_key):
        """Test successful web context fetching."""
        mock_get_api_key.return_value = "test-api-key"
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "• Market trend: Video ads growing 25% YoY\n• Audience insight: Gen Z prefers mobile-first content\n• Recent programming: Olympics driving premium inventory demand"
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].grounding_metadata = MagicMock()
        mock_response.candidates[0].grounding_metadata.web_search_queries = ["advertising trends 2024"]
        mock_response.candidates[0].grounding_metadata.grounding_chunks = [
            MagicMock(web=MagicMock(uri="https://example.com", title="Example Site"))
        ]
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        result = await fetch_web_context("test brief", 2000, 3, "gemini-2.5-flash", "google_search")
        
        assert len(result["snippets"]) > 0
        assert "Market trend" in result["snippets"][0]
        assert result["metadata"]["webSearchQueries"] == ["advertising trends 2024"]
        assert len(result["metadata"]["sources"]) == 1
    
    @patch('app.services.web_context_google.get_gemini_api_key')
    async def test_fetch_web_context_missing_api_key(self, mock_get_api_key):
        """Test web context fetching with missing API key."""
        mock_get_api_key.return_value = None
        
        with pytest.raises(RuntimeError, match="web grounding enabled but GEMINI_API_KEY missing"):
            await fetch_web_context("test brief", 2000, 3, "gemini-2.5-flash", "google_search")
    
    @patch('app.services.web_context_google.get_gemini_api_key')
    @patch('app.services.web_context_google.genai')
    async def test_fetch_web_context_timeout(self, mock_genai, mock_get_api_key):
        """Test web context fetching timeout."""
        mock_get_api_key.return_value = "test-api-key"
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = asyncio.TimeoutError()
        mock_genai.GenerativeModel.return_value = mock_model
        
        with pytest.raises(RuntimeError, match="web grounding timeout after 2000ms"):
            await fetch_web_context("test brief", 2000, 3, "gemini-2.5-flash", "google_search")
    
    @patch('app.services.web_context_google.get_gemini_api_key')
    @patch('app.services.web_context_google.genai')
    async def test_fetch_web_context_unsupported_model(self, mock_genai, mock_get_api_key):
        """Test web context fetching with unsupported model."""
        mock_get_api_key.return_value = "test-api-key"
        
        with pytest.raises(RuntimeError, match="web grounding unsupported for model 'gemini-1.0-pro'"):
            await fetch_web_context("test brief", 2000, 3, "gemini-1.0-pro", "google_search")


class TestOrchestratorIntegration:
    """Test orchestrator integration with web grounding."""
    
    @patch('app.services._orchestrator_agents.fetch_web_context')
    @patch('app.services._orchestrator_agents.MCPClient')
    @patch('app.utils.env.get_web_grounding_config')
    @patch('app.services.orchestrator.get_tenant_by_id')
    @patch('app.services.orchestrator.get_session')
    async def test_orchestrator_global_off_tenant_off(self, mock_get_session, mock_get_tenant, mock_get_config, mock_mcp_client, mock_fetch_web_context):
        """Test orchestrator when global flag is off and tenant is off."""
        from app.services.orchestrator import orchestrate_brief
        
        # Mock config with global flag off
        mock_get_config.return_value = {
            "enabled": False,
            "timeout_ms": 2000,
            "max_snippets": 3,
            "model": "gemini-2.5-flash",
            "provider": "google_search"
        }
        
        # Mock tenant with web context disabled
        mock_tenant = MagicMock()
        mock_tenant.slug = "test-publisher"
        mock_tenant.name = "Test Publisher"
        mock_tenant.enable_web_context = False
        mock_get_tenant.return_value = mock_tenant
        
        # Mock session context
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_get_session.return_value = iter([mock_session])
        
        # Mock MCP client
        mock_client = AsyncMock()
        mock_client.call.return_value = {"items": []}
        mock_mcp_client.return_value = mock_client
        
        # Call orchestrator
        result = await orchestrate_brief("test brief", [1], [])
        
        # Verify web context was not called
        mock_fetch_web_context.assert_not_called()
        
        # Verify MCP client was called without web snippets
        mock_client.call.assert_called_once()
        call_args = mock_client.call.call_args[0][1]  # Get the params
        assert "web_snippets" not in call_args
    
    @patch('app.services._orchestrator_agents.fetch_web_context')
    @patch('app.services._orchestrator_agents.MCPClient')
    @patch('app.utils.env.get_web_grounding_config')
    @patch('app.services.orchestrator.get_tenant_by_id')
    @patch('app.services.orchestrator.get_session')
    async def test_orchestrator_global_on_tenant_off(self, mock_get_session, mock_get_tenant, mock_get_config, mock_mcp_client, mock_fetch_web_context):
        """Test orchestrator when global flag is on but tenant is off."""
        from app.services.orchestrator import orchestrate_brief
        
        # Mock config with global flag on
        mock_get_config.return_value = {
            "enabled": True,
            "timeout_ms": 2000,
            "max_snippets": 3,
            "model": "gemini-2.5-flash",
            "provider": "google_search"
        }
        
        # Mock tenant with web context disabled
        mock_tenant = MagicMock()
        mock_tenant.slug = "test-publisher"
        mock_tenant.name = "Test Publisher"
        mock_tenant.enable_web_context = False
        mock_get_tenant.return_value = mock_tenant
        
        # Mock session context
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_get_session.return_value = iter([mock_session])
        
        # Mock MCP client
        mock_client = AsyncMock()
        mock_client.call.return_value = {"items": []}
        mock_mcp_client.return_value = mock_client
        
        # Call orchestrator
        result = await orchestrate_brief("test brief", [1], [])
        
        # Verify web context was not called
        mock_fetch_web_context.assert_not_called()
        
        # Verify MCP client was called without web snippets
        mock_client.call.assert_called_once()
        call_args = mock_client.call.call_args[0][1]  # Get the params
        assert "web_snippets" not in call_args
    
    @patch('app.services._orchestrator_agents.fetch_web_context')
    @patch('app.services._orchestrator_agents.MCPClient')
    @patch('app.utils.env.get_web_grounding_config')
    @patch('app.services.orchestrator.get_tenant_by_id')
    @patch('app.services.orchestrator.get_session')
    async def test_orchestrator_global_on_tenant_on(self, mock_get_session, mock_get_tenant, mock_get_config, mock_mcp_client, mock_fetch_web_context):
        """Test orchestrator when both global flag and tenant are on."""
        from app.services.orchestrator import orchestrate_brief
        
        # Mock config with global flag on
        mock_get_config.return_value = {
            "enabled": True,
            "timeout_ms": 2000,
            "max_snippets": 3,
            "model": "gemini-2.5-flash",
            "provider": "google_search"
        }
        
        # Mock tenant with web context enabled
        mock_tenant = MagicMock()
        mock_tenant.slug = "test-publisher"
        mock_tenant.name = "Test Publisher"
        mock_tenant.enable_web_context = True
        mock_get_tenant.return_value = mock_tenant
        
        # Mock session context
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_get_session.return_value = iter([mock_session])
        
        # Mock web context response
        mock_fetch_web_context.return_value = {
            "snippets": ["Market trend: Video ads growing 25% YoY"],
            "metadata": {"webSearchQueries": ["advertising trends"], "sources": []}
        }
        
        # Mock MCP client
        mock_client = AsyncMock()
        mock_client.call.return_value = {"items": []}
        mock_mcp_client.return_value = mock_client
        
        # Call orchestrator
        result = await orchestrate_brief("test brief", [1], [])
        
        # Verify web context was called
        mock_fetch_web_context.assert_called_once()
        
        # Verify MCP client was called with web snippets
        mock_client.call.assert_called_once()
        call_args = mock_client.call.call_args[0][1]  # Get the params
        assert "web_snippets" in call_args
        assert call_args["web_snippets"] == ["Market trend: Video ads growing 25% YoY"]
    
    @patch('app.services._orchestrator_agents.fetch_web_context')
    @patch('app.services._orchestrator_agents.MCPClient')
    @patch('app.utils.env.get_web_grounding_config')
    @patch('app.services.orchestrator.get_tenant_by_id')
    @patch('app.services.orchestrator.get_session')
    async def test_orchestrator_web_context_error(self, mock_get_session, mock_get_tenant, mock_get_config, mock_mcp_client, mock_fetch_web_context):
        """Test orchestrator when web context fails."""
        from app.services.orchestrator import orchestrate_brief
        
        # Mock config with global flag on
        mock_get_config.return_value = {
            "enabled": True,
            "timeout_ms": 2000,
            "max_snippets": 3,
            "model": "gemini-2.5-flash",
            "provider": "google_search"
        }
        
        # Mock tenant with web context enabled
        mock_tenant = MagicMock()
        mock_tenant.slug = "test-publisher"
        mock_tenant.name = "Test Publisher"
        mock_tenant.enable_web_context = True
        mock_get_tenant.return_value = mock_tenant
        
        # Mock session context
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=None)
        mock_get_session.return_value = iter([mock_session])
        
        # Mock web context error
        mock_fetch_web_context.side_effect = RuntimeError("web grounding quota or authorization error")
        
        # Mock MCP client
        mock_client = AsyncMock()
        mock_client.call.return_value = {"items": [{"product_id": 1, "reason": "test", "score": 0.8}]}
        mock_mcp_client.return_value = mock_client
        
        # Call orchestrator
        result = await orchestrate_brief("test brief", [1], [])
        
        # Verify web context was called
        mock_fetch_web_context.assert_called_once()
        
        # Verify MCP client was called without web snippets
        mock_client.call.assert_called_once()
        call_args = mock_client.call.call_args[0][1]  # Get the params
        assert "web_snippets" not in call_args
        
        # Verify result has web_context_unavailable error
        assert len(result["results"]) == 1
        assert result["results"][0]["ok"] is True
        assert "items" in result["results"][0]
        assert len(result["results"][0]["items"]) == 1
        assert "errors" in result["results"][0]["items"][0]
        assert "web_context_unavailable" in result["results"][0]["items"][0]["errors"]


class TestPublisherDashboard:
    """Test publisher dashboard web grounding integration."""
    
    @patch('app.routes.publisher.dashboard.get_tenant_by_slug')
    @patch('app.routes.publisher.dashboard.list_products')
    @patch('app.utils.env.get_web_grounding_config')
    def test_dashboard_shows_web_grounding_card(self, mock_get_config, mock_list_products, mock_get_tenant):
        """Test that dashboard shows web grounding card."""
        # Mock tenant
        mock_tenant = MagicMock()
        mock_tenant.name = "Test Publisher"
        mock_tenant.slug = "test-publisher"
        mock_tenant.enable_web_context = True
        mock_get_tenant.return_value = mock_tenant
        
        # Mock products
        mock_list_products.return_value = ([], 0)
        
        # Mock web config
        mock_get_config.return_value = {
            "enabled": True,
            "model": "gemini-2.5-flash"
        }
        
        response = client.get("/publisher/test-publisher/")
        
        assert response.status_code == 200
        assert "AI Enrichment Settings" in response.text
        assert "Enable Web Context Grounding" in response.text
        assert "checked" in response.text  # Should be checked since tenant has it enabled
        assert "Global: ON" in response.text
        assert "Model: gemini-2.5-flash" in response.text
    
    @patch('app.routes.publisher.dashboard.get_tenant_by_slug')
    @patch('app.routes.publisher.dashboard.update_tenant_web_context')
    def test_dashboard_update_web_context(self, mock_update_tenant, mock_get_tenant):
        """Test updating web context setting via dashboard."""
        # Mock tenant
        mock_tenant = MagicMock()
        mock_tenant.id = 1
        mock_get_tenant.return_value = mock_tenant
        
        # Mock update
        mock_update_tenant.return_value = mock_tenant
        
        response = client.post("/publisher/test-publisher/ai-enrichment", data={"enable_web_context": "on"}, follow_redirects=False)
        
        assert response.status_code == 302
        assert response.headers["location"] == "/publisher/test-publisher/"
        # The function is called with (session, tenant_id, enable_web_context)
        mock_update_tenant.assert_called_once()
        call_args = mock_update_tenant.call_args
        assert call_args[0][1] == 1  # tenant_id
        assert call_args[0][2] == True  # enable_web_context


class TestMCPIntegration:
    """Test MCP integration with web snippets."""
    
    @patch('app.services.mcp_rpc_handlers.get_tenant_by_slug')
    @patch('app.services.mcp_rpc_handlers.filter_products_for_brief')
    @patch('app.services.mcp_rpc_handlers.list_products')
    @patch('app.services.mcp_rpc_handlers.rank_products_with_ai')
    async def test_mcp_rank_products_with_web_snippets(self, mock_rank_ai, mock_list_products, mock_filter_products, mock_get_tenant):
        """Test MCP rank_products with web snippets."""
        from app.services.mcp_rpc_handlers import dispatch
        
        # Mock tenant
        mock_tenant = MagicMock()
        mock_tenant.id = 1
        mock_get_tenant.return_value = mock_tenant
        
        # Mock RAG results
        mock_filter_products.return_value = [{"product_id": 1, "rag_score": 0.8}]
        
        # Mock products
        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.name = "Test Product"
        mock_product.description = "Test Description"
        mock_product.delivery_type = "display"
        mock_product.price_cpm = 5.0
        mock_product.formats_json = None
        mock_product.targeting_json = None
        mock_list_products.return_value = ([mock_product], 1)
        
        # Mock AI ranking
        mock_rank_ai.return_value = [{"product_id": 1, "reason": "test", "score": 0.8}]
        
        # Call MCP with web snippets
        result = await dispatch("rank_products", {
            "brief": "test brief",
            "web_snippets": ["Market trend: Video ads growing"]
        }, "test-publisher", MagicMock())
        
        # Verify AI ranking was called with web snippets
        mock_rank_ai.assert_called_once()
        call_args = mock_rank_ai.call_args
        assert call_args[0][3] == ["Market trend: Video ads growing"]  # web_snippets parameter
    
    @patch('app.services.mcp_rpc_handlers.get_tenant_by_slug')
    async def test_mcp_rank_products_invalid_web_snippets(self, mock_get_tenant):
        """Test MCP rank_products with invalid web snippets."""
        from app.services.mcp_rpc_handlers import dispatch
        
        # Mock tenant
        mock_tenant = MagicMock()
        mock_get_tenant.return_value = mock_tenant
        
        # Call MCP with invalid web snippets
        with pytest.raises(Exception) as exc_info:
            await dispatch("rank_products", {
                "brief": "test brief",
                "web_snippets": "not a list"
            }, "test-publisher", MagicMock())
        
        assert "web_snippets must be a list of strings" in str(exc_info.value)
