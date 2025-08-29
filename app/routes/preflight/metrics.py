"""Preflight metrics calculation functions."""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.repos.external_agents import list_external_agents
from app.utils.reference_validator import get_salesagent_commit, get_signalsagent_commit

logger = logging.getLogger(__name__)


def get_tenant_prompt_metrics(db_session: Session) -> tuple[int, int]:
    """Get tenant custom prompt metrics."""
    try:
        # Check if custom_prompt column exists
        result = db_session.execute(text("PRAGMA table_info(tenant)"))
        columns = [row[1] for row in result.fetchall()]
        
        if "custom_prompt" not in columns:
            return 0, 0
        
        # Count tenants with custom prompts
        result = db_session.execute(
            text("SELECT COUNT(*) FROM tenant WHERE custom_prompt IS NOT NULL AND custom_prompt != ''")
        )
        with_custom = result.scalar() or 0
        
        # Count total tenants
        result = db_session.execute(text("SELECT COUNT(*) FROM tenant"))
        total = result.scalar() or 0
        
        return with_custom, total - with_custom
    except Exception:
        return 0, 0


def get_agent_metrics(db_session: Session) -> dict:
    """Get agent metrics."""
    enabled_sales = {"rest": 0, "mcp": 0}
    enabled_signals = {"rest": 0, "mcp": 0}
    
    try:
        external_agents = list_external_agents(db_session)
        
        for agent in external_agents:
            if not agent.enabled:
                continue
            
            if agent.agent_type == "sales":
                protocol = getattr(agent, 'protocol', 'mcp')
                enabled_sales[protocol] = enabled_sales.get(protocol, 0) + 1
            elif agent.agent_type == "signals":
                protocol = getattr(agent, 'protocol', 'mcp')
                enabled_signals[protocol] = enabled_signals.get(protocol, 0) + 1
    except Exception:
        pass
    
    return {
        "enabled_sales": enabled_sales,
        "enabled_signals": enabled_signals
    }


def get_reference_data() -> dict:
    """Get reference repository data."""
    try:
        salesagent_commit = get_salesagent_commit()
        signalsagent_commit = get_signalsagent_commit()
        reference_present = bool(salesagent_commit and signalsagent_commit)
    except Exception:
        salesagent_commit = ""
        signalsagent_commit = ""
        reference_present = False
    
    return {
        "salesagent_commit": salesagent_commit,
        "signalsagent_commit": signalsagent_commit,
        "present": reference_present
    }


def get_tenant_count(db_session: Session) -> int:
    """Get total tenant count."""
    try:
        result = db_session.execute(text("SELECT COUNT(*) FROM tenant"))
        return result.scalar() or 0
    except Exception:
        return 0

