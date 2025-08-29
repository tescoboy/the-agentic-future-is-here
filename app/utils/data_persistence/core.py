"""
Core utilities for data persistence.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Data directory for persistence files
DATA_DIR = Path("./data")
BACKUP_DIR = DATA_DIR / "backups"
SETTINGS_FILE = DATA_DIR / "app_settings.json"
EXTERNAL_AGENTS_FILE = DATA_DIR / "external_agents.json"
TENANT_SETTINGS_FILE = DATA_DIR / "tenant_settings.json"


def ensure_data_directories():
    """Ensure all data directories exist."""
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)
