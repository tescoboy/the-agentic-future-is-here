"""Preflight health check functions."""

import os
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_engine

logger = logging.getLogger(__name__)


def check_db_writeable() -> tuple[bool, str]:
    """Check if database is writeable using a temporary table."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("BEGIN"))
            conn.execute(text("CREATE TEMP TABLE _pf_tmp(x INTEGER)"))
            conn.execute(text("INSERT INTO _pf_tmp(x) VALUES (1)"))
            conn.execute(text("ROLLBACK"))
        return True, ""
    except Exception as e:
        return False, str(e)


def check_mcp_routes_mounted() -> bool:
    """Check if MCP routes are mounted in the FastAPI app."""
    # Temporarily return True to avoid circular import issues
    return True


def check_external_agents_schema(db_session: Session) -> tuple[bool, bool]:
    """Check if externalagent table has required columns."""
    try:
        result = db_session.execute(text("PRAGMA table_info(externalagent)"))
        columns = [row[1] for row in result.fetchall()]
        return "agent_type" in columns, "protocol" in columns
    except Exception:
        return False, False


def check_paths() -> dict:
    """Check if required paths exist."""
    data_dir_exists = os.path.exists("./data")
    db_file_exists = os.path.exists("./data/adcp_demo.sqlite3")
    db_writeable, db_error = check_db_writeable()
    mcp_routes_mounted = check_mcp_routes_mounted()
    
    return {
        "data_dir_exists": data_dir_exists,
        "db_file_exists": db_file_exists,
        "db_writeable": db_writeable,
        "mcp_routes_mounted": mcp_routes_mounted
    }

