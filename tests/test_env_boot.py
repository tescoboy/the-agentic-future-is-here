"""
Phase 0 environment boot tests.
Validates health endpoint and data directory creation.
"""

import pytest
import sys
from pathlib import Path
import os

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.db import ensure_database


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test that health endpoint returns correct response."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["service"] == "adcp-demo"


def test_data_directory_exists(client):
    """Test that data directory exists after startup."""
    # Manually trigger database initialization
    ensure_database()
    
    data_dir = Path("./data")
    assert data_dir.exists(), "Data directory should exist after startup"
    assert data_dir.is_dir(), "Data directory should be a directory"


def test_database_file_created(client):
    """Test that database file is created."""
    # Manually trigger database initialization
    ensure_database()
    
    db_path = Path("./data/adcp_demo.sqlite3")
    assert db_path.exists(), "Database file should be created"
