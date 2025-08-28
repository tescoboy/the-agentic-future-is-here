"""
External agent repository operations.
"""

from typing import List, Optional
from sqlmodel import Session, select
from app.models import ExternalAgent


def create_external_agent(session: Session, name: str, base_url: str, 
                         enabled: bool = True, agent_type: str = "sales", 
                         protocol: str = "rest") -> ExternalAgent:
    """Create a new external agent."""
    # Validate base_url
    if not base_url.startswith(("http://", "https://")):
        raise ValueError(f"base_url must start with http:// or https://. Got: {base_url[:200]}")
    
    agent = ExternalAgent(
        name=name,
        base_url=base_url,
        enabled=enabled,
        agent_type=agent_type,
        protocol=protocol
    )
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


def get_external_agent_by_id(session: Session, agent_id: int) -> Optional[ExternalAgent]:
    """Get external agent by ID."""
    return session.get(ExternalAgent, agent_id)


def list_external_agents(session: Session, enabled_only: bool = False) -> List[ExternalAgent]:
    """List external agents."""
    statement = select(ExternalAgent)
    if enabled_only:
        statement = statement.where(ExternalAgent.enabled == True)
    return session.exec(statement).all()


def list_by_type(session: Session, agent_type: str) -> List[ExternalAgent]:
    """List external agents by type."""
    statement = select(ExternalAgent).where(ExternalAgent.agent_type == agent_type)
    return session.exec(statement).all()


def list_by_type_protocol(session: Session, agent_type: str, protocol: str) -> List[ExternalAgent]:
    """List external agents by type and protocol."""
    statement = select(ExternalAgent).where(
        ExternalAgent.agent_type == agent_type,
        ExternalAgent.protocol == protocol
    )
    return session.exec(statement).all()


def update_external_agent(session: Session, agent_id: int, name: str, base_url: str, 
                         enabled: bool, agent_type: str, protocol: str) -> Optional[ExternalAgent]:
    """Update an external agent."""
    agent = get_external_agent_by_id(session, agent_id)
    if not agent:
        return None
    
    # Validate base_url
    if not base_url.startswith(("http://", "https://")):
        raise ValueError(f"base_url must start with http:// or https://. Got: {base_url[:200]}")
    
    agent.name = name
    agent.base_url = base_url
    agent.enabled = enabled
    agent.agent_type = agent_type
    agent.protocol = protocol
    
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent


def delete_external_agent(session: Session, agent_id: int) -> bool:
    """Delete an external agent."""
    agent = get_external_agent_by_id(session, agent_id)
    if not agent:
        return False
    
    session.delete(agent)
    session.commit()
    return True

