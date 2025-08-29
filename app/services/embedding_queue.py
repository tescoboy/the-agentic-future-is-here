"""
Async embedding queue system for background processing.
Handles product embedding jobs with concurrency control and retry logic.
"""

import asyncio
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.utils.embeddings_config import get_embeddings_config
from app.utils.embeddings import batch_embed_text
from app.db import get_session

logger = logging.getLogger(__name__)


class EmbeddingQueue:
    """
    In-memory async queue for product embedding jobs.
    Handles deduplication, batching, and retry logic.
    """
    
    def __init__(self):
        self._queue: List[int] = []  # FIFO list for processing order
        self._enqueued: set[int] = set()  # Set for deduplication
        self._in_progress: set[int] = set()  # Currently processing
        self._completed_since_boot: int = 0
        self._failed_since_boot: int = 0
        self._retry_counts: Dict[int, int] = {}  # In-memory retry tracking
        self._last_errors: Dict[int, str] = {}  # In-memory error tracking
        self._worker_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Get configuration
        config = get_embeddings_config()
        self._concurrency = config['concurrency']
        self._batch_size = config['batch_size']
        self._semaphore = asyncio.Semaphore(self._concurrency)
        
        logger.info(f"EmbeddingQueue initialized: concurrency={self._concurrency}, batch_size={self._batch_size}")
    
    def enqueue_product_ids(self, product_ids: List[int]) -> int:
        """
        Enqueue product IDs for embedding processing.
        
        Args:
            product_ids: List of product IDs to embed
            
        Returns:
            Number of newly enqueued items (after deduplication)
        """
        if not product_ids:
            return 0
        
        # Clamp batch size to prevent flood
        max_batch = self._batch_size * 10
        if len(product_ids) > max_batch:
            logger.warning(f"Enqueue batch size {len(product_ids)} exceeds limit {max_batch}, trimming")
            product_ids = product_ids[:max_batch]
        
        # Deduplicate and count newly enqueued items
        newly_enqueued = 0
        for product_id in product_ids:
            if product_id not in self._enqueued:
                self._enqueued.add(product_id)
                self._queue.append(product_id)
                newly_enqueued += 1
        
        if newly_enqueued > 0:
            logger.info(f"Enqueued {newly_enqueued} new product IDs for embedding")
        
        return newly_enqueued
    
    def stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue metrics
        """
        return {
            'pending': len(self._queue),
            'in_progress': len(self._in_progress),
            'completed_since_boot': self._completed_since_boot,
            'failed_since_boot': self._failed_since_boot,
            'retry_count': sum(self._retry_counts.values())
        }
    
    async def run_worker(self) -> None:
        """
        Main worker loop for processing embedding jobs.
        Handles batching, concurrency, and retry logic.
        """
        logger.info("Embedding worker started")
        
        while not self._shutdown_event.is_set():
            try:
                # Get next batch of products
                batch = self._get_next_batch()
                if not batch:
                    await asyncio.sleep(1)  # Wait for more work
                    continue
                
                # Process batch with concurrency control
                await self._process_batch(batch)
                
            except asyncio.CancelledError:
                logger.info("Embedding worker cancelled")
                break
            except Exception as e:
                logger.error(f"Embedding worker error: {e}")
                await asyncio.sleep(5)  # Back off on errors
        
        # Log final stats on shutdown
        stats = self.stats()
        logger.info(f"Embedding worker stopped: pending={stats['pending']}, "
                   f"in_progress={stats['in_progress']}, completed={stats['completed_since_boot']}, "
                   f"failed={stats['failed_since_boot']}")
    
    def _get_next_batch(self) -> List[int]:
        """Get next batch of product IDs from queue."""
        batch = []
        while len(batch) < self._batch_size and self._queue:
            product_id = self._queue.pop(0)
            if product_id in self._enqueued:  # Extra safety check
                self._enqueued.remove(product_id)
                self._in_progress.add(product_id)
                batch.append(product_id)
        
        return batch
    
    async def _process_batch(self, product_ids: List[int]) -> None:
        """Process a batch of product IDs with concurrency control."""
        async with self._semaphore:
            try:
                await self._embed_batch(product_ids)
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                # Mark all products in batch as failed
                for product_id in product_ids:
                    self._mark_failed(product_id, str(e))
    
    async def _embed_batch(self, product_ids: List[int]) -> None:
        """Embed a batch of products with retry logic."""
        session = next(get_session())
        
        try:
            # Get product texts for embedding
            product_texts = await self._get_product_texts(session, product_ids)
            if not product_texts:
                return
            
            # Generate embeddings
            embeddings = await batch_embed_text(list(product_texts.values()))
            if not embeddings:
                raise RuntimeError("Failed to generate embeddings")
            
            # Store embeddings
            await self._store_embeddings(session, product_ids, product_texts, embeddings)
            
            # Mark as completed
            for product_id in product_ids:
                self._mark_completed(product_id)
                
        finally:
            session.close()
    
    async def _get_product_texts(self, session, product_ids: List[int]) -> Dict[int, str]:
        """Get product texts for embedding."""
        from app.models import Product
        
        products = session.query(Product).filter(Product.id.in_(product_ids)).all()
        return {p.id: f"{p.name}\n{p.description}" for p in products}
    
    async def _store_embeddings(self, session, product_ids: List[int], 
                               product_texts: Dict[int, str], embeddings: List[List[float]]) -> None:
        """Store embeddings in database."""
        from app.utils.embeddings import upsert_product_embeddings
        
        config = get_embeddings_config()
        now = datetime.utcnow().isoformat()
        
        for i, product_id in enumerate(product_ids):
            if i < len(embeddings):
                embedding = embeddings[i]
                embedding_text = product_texts[product_id]
                
                # Create embedding hash including metadata
                hash_input = f"{embedding_text}:{config['provider']}:{config['model']}:{len(embedding)}"
                embedding_hash = hashlib.sha256(hash_input.encode()).hexdigest()
                
                # Store embedding with metadata
                await upsert_product_embeddings(
                    session, product_id, embedding, 
                    provider=config['provider'],
                    model=config['model'],
                    dim=len(embedding),
                    updated_at=now,
                    embedding_hash=embedding_hash
                )
    
    def _mark_completed(self, product_id: int) -> None:
        """Mark a product as completed."""
        self._in_progress.discard(product_id)
        self._completed_since_boot += 1
        self._retry_counts.pop(product_id, None)
        self._last_errors.pop(product_id, None)
    
    def _mark_failed(self, product_id: int, error: str) -> None:
        """Mark a product as failed with retry logic."""
        self._in_progress.discard(product_id)
        
        # Check retry count
        retry_count = self._retry_counts.get(product_id, 0)
        if retry_count < 2:  # Max 2 retries
            # Re-queue for retry with exponential backoff
            retry_count += 1
            self._retry_counts[product_id] = retry_count
            self._last_errors[product_id] = error
            
            # Add back to queue with delay
            asyncio.create_task(self._retry_with_delay(product_id, retry_count))
            logger.warning(f"Product {product_id} failed, retry {retry_count}/2: {error}")
        else:
            # Max retries exceeded
            self._failed_since_boot += 1
            logger.error(f"Product {product_id} failed permanently after {retry_count} retries: {error}")
    
    async def _retry_with_delay(self, product_id: int, retry_count: int) -> None:
        """Retry a product with exponential backoff."""
        delay = min(2 ** retry_count, 4)  # 1s, 2s, capped at 4s
        await asyncio.sleep(delay)
        
        # Re-add to queue if not shutting down
        if not self._shutdown_event.is_set():
            self._enqueued.add(product_id)
            self._queue.append(product_id)
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the worker."""
        logger.info("Shutting down embedding worker...")
        self._shutdown_event.set()
        
        if self._worker_task:
            try:
                await asyncio.wait_for(self._worker_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Worker shutdown timeout, forcing cancellation")
                self._worker_task.cancel()


# Global queue instance
_embedding_queue: Optional[EmbeddingQueue] = None


def get_embedding_queue() -> EmbeddingQueue:
    """Get the global embedding queue instance."""
    global _embedding_queue
    if _embedding_queue is None:
        _embedding_queue = EmbeddingQueue()
    return _embedding_queue


async def start_worker(app) -> None:
    """Start the embedding worker on app startup."""
    if not get_embeddings_config()['enabled']:
        logger.info("Embeddings disabled, skipping worker startup")
        return
    
    queue = get_embedding_queue()
    queue._worker_task = asyncio.create_task(queue.run_worker())
    logger.info("Embedding worker started")


async def shutdown_worker() -> None:
    """Shutdown the embedding worker."""
    global _embedding_queue
    if _embedding_queue:
        await _embedding_queue.shutdown()
        _embedding_queue = None
