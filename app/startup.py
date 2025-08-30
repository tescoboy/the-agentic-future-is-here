"""
Application startup and shutdown logic.
"""

import logging
from pathlib import Path
from app.db import ensure_database, create_all_tables, get_session
from app.utils.migrations import run_migrations
from app.utils.rag_migrations import run_rag_startup_checks

logger = logging.getLogger(__name__)

async def startup_event():
    """Initialize application on startup."""
    try:
        # 1. Skip reference validation in production
        logger.info("Skipping reference repository validation (production mode)")
        
        # 2. Ensure data directory exists and test persistent disk
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        
        # Test persistent disk functionality
        try:
            from app.utils.data_persistence.backup import test_persistent_disk
            disk_test_result = test_persistent_disk()
            logger.info(f"Persistent disk test: {disk_test_result}")
        except Exception as e:
            logger.warning(f"Persistent disk test failed: {e}")
        
        # 3. Create base tables
        create_all_tables()
        
        # 4. Run migrations
        run_migrations()
        
        # 5. Initialize database connection
        ensure_database()
        
        # 6. Run embeddings migrations
        try:
            from app.utils.embeddings_migrations import run_embeddings_migrations
            session = next(get_session())
            run_embeddings_migrations(session)
            logger.info("Embeddings migrations completed successfully")
        except Exception as e:
            logger.warning(f"Embeddings migrations failed: {e}")
        finally:
            if 'session' in locals():
                session.close()
        
        # 7. Run RAG startup checks
        try:
            session = next(get_session())
            from sqlalchemy import text
            result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='product'"))
            if result.fetchone():
                run_rag_startup_checks(session)
                logger.info("RAG startup checks completed successfully")
            else:
                logger.warning("Product table not found, skipping RAG startup checks")
        except Exception as e:
            logger.warning(f"RAG startup checks failed (will retry later): {e}")
        finally:
            if 'session' in locals():
                session.close()
        
        # 8. Auto-backup and restore
        try:
            from app.utils.data_persistence import auto_backup_on_startup, auto_restore_on_startup
            session = next(get_session())
            auto_backup_on_startup(session)
            auto_restore_on_startup(session)
            logger.info("Backup/restore operations completed successfully")
        except Exception as e:
            logger.warning(f"Backup/restore operations failed: {e}")
        finally:
            if 'session' in locals():
                session.close()
        
        # 9. Seed test data - DISABLED: Using backup JSON method instead
        # try:
        #     from app.utils.seed_data import seed_test_data
        #     session = next(get_session())
        #     seed_test_data(session)
        #     logger.info("Test data seeding completed successfully")
        # except Exception as e:
        #     logger.warning(f"Test data seeding failed: {e}")
        # finally:
        #     if 'session' in locals():
        #         session.close()
        
        # 10. Start embedding worker (commented out - requires app instance)
        # try:
        #     from app.services.embedding_queue import start_worker
        #     await start_worker(app)
        # except Exception as e:
        #     logger.warning(f"Failed to start embedding worker: {e}")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

async def shutdown_event():
    """Cleanup on application shutdown."""
    try:
        from app.services.embedding_queue import shutdown_worker
        await shutdown_worker()
        logger.info("Embedding worker shutdown completed")
    except Exception as e:
        logger.warning(f"Embedding worker shutdown failed: {e}")
