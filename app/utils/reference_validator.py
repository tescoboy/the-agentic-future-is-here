"""
Reference repository validation utilities.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict


def validate_reference_repos(base_path: str = "./reference") -> Dict[str, str]:
    """
    Validate reference repositories exist and return commit hashes.
    
    Args:
        base_path: Base path for reference repositories
        
    Returns:
        dict: {"salesagent": "<hash>", "signals-agent": "<hash>"}
        
    Raises:
        RuntimeError: If repos missing or invalid, with clone instructions
    """
    # Check if git is available
    if not shutil.which("git"):
        raise RuntimeError(
            "Git is not installed. Install git and then run:\n"
            "git clone https://github.com/adcontextprotocol/salesagent reference/salesagent\n"
            "git clone https://github.com/adcontextprotocol/signals-agent reference/signals-agent"
        )
    
    # Define required repos
    repos = {
        "salesagent": Path(base_path) / "salesagent",
        "signals-agent": Path(base_path) / "signals-agent"
    }
    
    # Check if all repos exist and are valid git repositories
    missing_repos = []
    for name, repo_path in repos.items():
        if not repo_path.exists() or not _is_valid_git_repo(repo_path):
            missing_repos.append(name)
    
    if missing_repos:
        raise RuntimeError(
            "Missing reference repos. Clone them exactly as follows:\n"
            "git clone https://github.com/adcontextprotocol/salesagent reference/salesagent\n"
            "git clone https://github.com/adcontextprotocol/signals-agent reference/signals-agent"
        )
    
    # Get commit hashes
    hashes = {}
    for name, repo_path in repos.items():
        hash_value = _get_git_hash(repo_path)
        if not _is_valid_hash(hash_value):
            raise RuntimeError(
                "Invalid reference repos. Clone them exactly as follows:\n"
                "git clone https://github.com/adcontextprotocol/salesagent reference/salesagent\n"
                "git clone https://github.com/adcontextprotocol/signals-agent reference/signals-agent"
            )
        hashes[name] = hash_value
    
    return hashes


def _is_valid_git_repo(repo_path: Path) -> bool:
    """Check if path is a valid git repository."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _get_git_hash(repo_path: Path) -> str:
    """Get short git hash for repository."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


def _is_valid_hash(hash_value: str) -> bool:
    """Validate git hash format."""
    pattern = r"^[0-9a-f]{7,12}$"
    return bool(re.match(pattern, hash_value))


def get_salesagent_commit() -> str:
    """Get salesagent commit hash."""
    try:
        hashes = validate_reference_repos()
        return hashes.get("salesagent", "")
    except Exception:
        return ""


def get_signalsagent_commit() -> str:
    """Get signals-agent commit hash."""
    try:
        hashes = validate_reference_repos()
        return hashes.get("signals-agent", "")
    except Exception:
        return ""
