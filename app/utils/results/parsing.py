"""Results parsing utilities."""

from typing import List, Tuple, Any
from sqlalchemy.orm import Session

from app.repos.external_agents import get_external_agent_by_id


def parse_agent_selections(agents_list: List[str], db_session: Session = None) -> Tuple[List[int], List[Any]]:
    """
    Parse agent selection list into tenant_ids and external_agents.
    
    Args:
        agents_list: List of agent strings like ["sales:tenant:1", "signals:external:2"]
        
    Returns:
        Tuple of (tenant_ids, external_agents)
        
    Raises:
        ValueError: If malformed agent value encountered
    """
    tenant_ids = []
    external_agents = []
    
    for agent_str in agents_list:
        try:
            parts = agent_str.split(":")
            if len(parts) != 3:
                raise ValueError(f"Invalid agent format: {agent_str}")
            
            agent_type, source, agent_id = parts
            
            if agent_type == "sales" and source == "tenant":
                tenant_ids.append(int(agent_id))
            elif agent_type == "signals" and source == "external":
                if db_session:
                    try:
                        external_agent = get_external_agent_by_id(db_session, int(agent_id))
                        if external_agent:
                            external_agents.append(external_agent)
                    except Exception:
                        # Skip invalid external agents
                        pass
            elif agent_type == "sales" and source == "external":
                # Reserve for future external sales support
                if db_session:
                    try:
                        external_agent = get_external_agent_by_id(db_session, int(agent_id))
                        if external_agent and external_agent.agent_type == "sales":
                            external_agents.append(external_agent)
                    except Exception:
                        # Skip invalid external agents
                        pass
            else:
                raise ValueError(f"Unsupported agent type: {agent_str}")
                
        except (ValueError, IndexError) as e:
            raise ValueError(f"Malformed agent value: {agent_str}") from e
    
    return tenant_ids, external_agents

