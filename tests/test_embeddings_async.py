"""
Tests for async embeddings system.
Covers queue behavior, backfill, and integration scenarios.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.utils.embeddings_config import get_embeddings_config, is_embeddings_enabled
from app.services.embedding_queue import EmbeddingQueue, get_embedding_queue
from app.services.embeddings_backfill import find_products_needing_embeddings, backfill_once, get_vector_counts
from app.db import get_session
from app.models import Product, Tenant


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.sqlite3')
    os.close(fd)
    
    engine = create_engine(f"sqlite:///{path}")
    
    # Create tables
    from app.models import SQLModel
    SQLModel.metadata.create_all(engine)
    
    # Run embeddings migrations to create product_embeddings table
    from app.utils.embeddings_migrations import run_embeddings_migrations
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    run_embeddings_migrations(session)
    session.close()
    
    yield SessionLocal()
    
    # Cleanup
    os.unlink(path)


@pytest.fixture
def test_tenant(temp_db):
    """Create a test tenant."""
    tenant = Tenant(
        slug="test-tenant",
        name="Test Tenant",
        custom_prompt=None
    )
    temp_db.add(tenant)
    temp_db.commit()
    return tenant


@pytest.fixture
def test_products(temp_db, test_tenant):
    """Create test products for embedding."""
    products = []
    for i in range(16):
        product = Product(
            tenant_id=test_tenant.id,
            name=f"Test Product {i}",
            description=f"Description for test product {i} with brand names and quoted phrases",
            price_cpm=10.0 + i,
            delivery_type="streaming",
            formats_json='{"video": true}',
            targeting_json='{"age": "25-35"}'
        )
        temp_db.add(product)
        products.append(product)
    
    temp_db.commit()
    return products


@pytest.fixture
def mock_embeddings_config():
    """Mock embeddings configuration."""
    with patch.dict(os.environ, {
        'EMBEDDINGS_PROVIDER': 'gemini',
        'GEMINI_API_KEY': 'test-key',
        'EMBEDDINGS_MODEL': 'text-embedding-004',
        'EMB_CONCURRENCY': '2',
        'EMB_BATCH_SIZE': '8'
    }):
        yield


@pytest.fixture
def mock_batch_embed_text():
    """Mock batch embedding function."""
    with patch('app.utils.embeddings.batch_embed_text') as mock:
        # Return small fixed vectors for testing
        async def mock_embed(texts):
            return [[0.1] * 8 for _ in range(len(texts))]  # 8-dim vectors
        mock.side_effect = mock_embed
        yield mock


class TestEmbeddingsConfiguration:
    """Test embeddings configuration."""
    
    def test_embeddings_disabled_by_default(self):
        """Test that embeddings are disabled when no provider is set."""
        with patch.dict(os.environ, {}, clear=True):
            assert not is_embeddings_enabled()
    
    def test_embeddings_enabled_with_provider(self, mock_embeddings_config):
        """Test that embeddings are enabled when provider is set."""
        assert is_embeddings_enabled()
    
    def test_config_validation_missing_key(self):
        """Test that missing API key raises error."""
        with patch.dict(os.environ, {
            'EMBEDDINGS_PROVIDER': 'gemini',
            # No GEMINI_API_KEY
        }, clear=True):
            with pytest.raises(RuntimeError, match="embeddings provider configured but GEMINI_API_KEY missing"):
                get_embeddings_config()
    
    def test_config_clamping(self):
        """Test that configuration values are clamped correctly."""
        with patch.dict(os.environ, {
            'EMBEDDINGS_PROVIDER': 'gemini',
            'GEMINI_API_KEY': 'test-key',
            'EMB_CONCURRENCY': '10',  # Should be clamped to 8
            'EMB_BATCH_SIZE': '200'   # Should be clamped to 128
        }):
            config = get_embeddings_config()
            assert config['concurrency'] == 8
            assert config['batch_size'] == 128


class TestEmbeddingQueue:
    """Test embedding queue functionality."""
    
    def test_queue_initialization(self, mock_embeddings_config):
        """Test queue initialization with configuration."""
        queue = EmbeddingQueue()
        assert queue._concurrency == 2
        assert queue._batch_size == 8
    
    def test_enqueue_deduplication(self, mock_embeddings_config):
        """Test that duplicate product IDs are deduplicated."""
        queue = EmbeddingQueue()
        
        # Enqueue same product multiple times
        result1 = queue.enqueue_product_ids([1, 2, 3])
        result2 = queue.enqueue_product_ids([2, 3, 4])
        result3 = queue.enqueue_product_ids([1, 2, 3])
        
        assert result1 == 3  # First enqueue: 3 new items
        assert result2 == 1  # Second enqueue: 1 new item (4)
        assert result3 == 0  # Third enqueue: 0 new items (all duplicates)
        
        assert len(queue._queue) == 4  # Total unique items
        assert queue._enqueued == {1, 2, 3, 4}
    
    def test_batch_size_clamping(self, mock_embeddings_config):
        """Test that large batches are clamped."""
        queue = EmbeddingQueue()
        
        # Try to enqueue more than max_batch (batch_size * 10 = 80)
        large_batch = list(range(100))
        result = queue.enqueue_product_ids(large_batch)
        
        assert result == 80  # Only first 80 items enqueued
        assert len(queue._queue) == 80
    
    def test_queue_stats(self, mock_embeddings_config):
        """Test queue statistics."""
        queue = EmbeddingQueue()
        
        # Enqueue some items
        queue.enqueue_product_ids([1, 2, 3])
        
        stats = queue.stats()
        assert stats['pending'] == 3
        assert stats['in_progress'] == 0
        assert stats['completed_since_boot'] == 0
        assert stats['failed_since_boot'] == 0
    
    @pytest.mark.asyncio
    async def test_worker_processing(self, mock_embeddings_config, mock_batch_embed_text, temp_db, test_products):
        """Test worker processing of batches."""
        queue = EmbeddingQueue()
        
        # Enqueue products
        product_ids = [p.id for p in test_products[:8]]
        queue.enqueue_product_ids(product_ids)
        
        # Mock the database session and embedding function
        with patch('app.services.embedding_queue.get_session') as mock_get_session, \
             patch('app.services.embedding_queue.batch_embed_text') as mock_embed:
            mock_get_session.return_value = iter([temp_db])
            mock_embed.return_value = [[0.1] * 8 for _ in range(4)]
            
            # Process one batch
            await queue._process_batch(product_ids[:4])
            
            # Check that products were processed
            assert queue._completed_since_boot == 4
            assert len(queue._in_progress) == 0
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_embeddings_config):
        """Test retry logic with exponential backoff."""
        queue = EmbeddingQueue()
        
        # Mock a failed embedding
        with patch.object(queue, '_embed_batch', side_effect=Exception("API Error")):
            await queue._process_batch([1])
            
            # Check retry count
            assert queue._retry_counts[1] == 1
            assert queue._failed_since_boot == 0  # Not failed yet, just retrying
            
            # Simulate second failure
            await queue._process_batch([1])
            assert queue._retry_counts[1] == 2
            assert queue._failed_since_boot == 0  # Still retrying
            
            # Simulate third failure (max retries exceeded)
            await queue._process_batch([1])
            assert queue._failed_since_boot == 1  # Now marked as failed


class TestBackfillService:
    """Test backfill service functionality."""
    
    def test_find_products_needing_embeddings(self, mock_embeddings_config, temp_db, test_products):
        """Test finding products that need embeddings."""
        # All products should need embeddings initially
        product_ids = find_products_needing_embeddings(temp_db, limit=10)
        assert len(product_ids) == 10
        assert all(pid in [p.id for p in test_products] for pid in product_ids)
    
    def test_pagination(self, mock_embeddings_config, temp_db, test_products):
        """Test pagination in find_products_needing_embeddings."""
        # Get first page
        page1 = find_products_needing_embeddings(temp_db, limit=5, last_seen_id=0)
        assert len(page1) == 5
        
        # Get second page
        page2 = find_products_needing_embeddings(temp_db, limit=5, last_seen_id=max(page1))
        assert len(page2) == 5
        
        # No overlap
        assert not set(page1).intersection(set(page2))
    
    @pytest.mark.asyncio
    async def test_backfill_once(self, mock_embeddings_config, mock_batch_embed_text, temp_db, test_products):
        """Test backfill processing."""
        result = await backfill_once(temp_db, batch_size=4)
        
        assert result['processed'] == 4
        assert result['successful'] == 4
        assert result['failed'] == 0
        assert result['remaining'] > 0  # More products still need embeddings
    
    def test_vector_counts(self, mock_embeddings_config, temp_db):
        """Test vector count calculations."""
        counts = get_vector_counts(temp_db)
        assert counts['vector_count_current_model'] == 0
        assert counts['vector_count_all'] == 0


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_embeddings_disabled_scenario(self, temp_db, test_products):
        """Test behavior when embeddings are disabled."""
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise errors
            assert not is_embeddings_enabled()
            
            # Queue should not be created
            with pytest.raises(RuntimeError):
                get_embedding_queue()
    
    @pytest.mark.asyncio
    async def test_missing_api_key_scenario(self, temp_db, test_products):
        """Test behavior when API key is missing."""
        with patch.dict(os.environ, {
            'EMBEDDINGS_PROVIDER': 'gemini',
            # No GEMINI_API_KEY
        }):
            with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
                get_embeddings_config()
    
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, mock_embeddings_config, temp_db, test_products):
        """Test rate limit retry scenario."""
        queue = EmbeddingQueue()
        
        # Mock batch_embed_text to fail with 429, then succeed
        with patch('app.utils.embeddings.batch_embed_text') as mock_embed:
            mock_embed.side_effect = [
                Exception("429 Rate Limited"),  # First call fails
                [[0.1] * 8 for _ in range(4)]   # Second call succeeds
            ]
            
            with patch('app.services.embedding_queue.get_session') as mock_get_session:
                mock_get_session.return_value = iter([temp_db])
                
                # Process batch - should retry and succeed
                await queue._process_batch([test_products[0].id])
                
                # Should have retried once
                assert queue._retry_counts[test_products[0].id] == 1
                # But ultimately succeeded
                assert queue._completed_since_boot == 1
                assert queue._failed_since_boot == 0
    
    @pytest.mark.asyncio
    async def test_bulk_import_scenario(self, mock_embeddings_config, mock_batch_embed_text, temp_db, test_tenant):
        """Test bulk import scenario with 120 products."""
        # Create 120 products
        products = []
        for i in range(120):
            product = Product(
                tenant_id=test_tenant.id,
                name=f"Bulk Product {i}",
                description=f"Description for bulk product {i}",
                price_cpm=10.0 + i,
                delivery_type="streaming",
                formats_json='{"video": true}',
                targeting_json='{"age": "25-35"}'
            )
            temp_db.add(product)
            products.append(product)
        temp_db.commit()
        
        # Enqueue all products
        queue = get_embedding_queue()
        product_ids = [p.id for p in products]
        enqueued = queue.enqueue_product_ids(product_ids)
        
        assert enqueued == 120
        assert queue.stats()['pending'] == 120
        
        # Process in batches
        with patch('app.services.embedding_queue.get_session') as mock_get_session:
            mock_get_session.return_value = iter([temp_db])
            
            # Process all batches
            while queue.stats()['pending'] > 0:
                batch = queue._get_next_batch()
                if batch:
                    await queue._process_batch(batch)
            
            # All products should be processed
            stats = queue.stats()
            assert stats['pending'] == 0
            assert stats['completed_since_boot'] == 120
            assert stats['failed_since_boot'] == 0


class TestDatabaseSchema:
    """Test database schema changes."""
    
    def test_embeddings_table_schema(self, temp_db):
        """Test that embeddings table has correct schema."""
        # Check if table exists and has required columns
        from sqlalchemy import text
        result = temp_db.execute(text("PRAGMA table_info(product_embeddings)"))
        columns = {row[1] for row in result.fetchall()}
        
        required_columns = {
            'id', 'product_id', 'embedding_text', 'embedding_hash', 
            'embedding', 'provider', 'model', 'dim', 'updated_at', 
            'is_stale', 'created_at'
        }
        
        assert required_columns.issubset(columns)
    
    def test_unique_index(self, temp_db):
        """Test unique index on (product_id, provider, model)."""
        # Check if unique index exists
        from sqlalchemy import text
        result = temp_db.execute(text("PRAGMA index_list(product_embeddings)"))
        indexes = {row[1] for row in result.fetchall()}
        
        assert 'idx_product_embeddings_version' in indexes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
