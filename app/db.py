"""
Database configuration and session management for AdCP Demo.
Handles SQLite persistence with proper FastAPI integration.
"""

import os
from pathlib import Path
from typing import Generator
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy import event, text


def get_engine():
    """Get database engine with environment-based configuration."""
    db_url = os.getenv("DB_URL", "sqlite:///./data/adcp_demo.sqlite3")
    
    if db_url.startswith("sqlite"):
        # SQLite-specific configuration for FastAPI compatibility
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False
        )
        
        # Enable foreign key support for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        engine = create_engine(db_url, echo=False)
    
    return engine


def create_all_tables():
    """Create all database tables."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def ensure_database():
    """Ensure database directory exists and database file is created."""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        
        # Touch the database file to ensure it exists
        engine = get_engine()
        db_url = os.getenv("DB_URL", "sqlite:///./data/adcp_demo.sqlite3")
        
        if db_url.startswith("sqlite"):
            db_path = db_url.replace("sqlite:///", "")
            if not db_path.startswith("/"):
                db_path = f"./{db_path}"
            Path(db_path).touch(exist_ok=True)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
    except Exception as e:
        raise RuntimeError(f"Database initialization failed: {str(e)}")


def migrate_web_context_column():
    """Add enable_web_context column to tenant table if it doesn't exist."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(tenant)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'enable_web_context' not in columns:
                # Add the column
                conn.execute(text("ALTER TABLE tenant ADD COLUMN enable_web_context INTEGER DEFAULT 0"))
                conn.commit()
                print("Added enable_web_context column to tenant table")
            else:
                print("enable_web_context column already exists")
                
    except Exception as e:
        raise RuntimeError(f"Database migration failed: ALTER TABLE tenant ADD COLUMN enable_web_context INTEGER DEFAULT 0 - {str(e)}")


def get_session() -> Generator[Session, None, None]:
    """Get database session for dependency injection."""
    engine = get_engine()
    with Session(engine) as session:
        yield session
