"""
External agents routes for admin interface.
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.db import get_session
from app.repos.external_agents import (
    create_external_agent, get_external_agent_by_id, list_external_agents,
    update_external_agent, delete_external_agent
)
from app.utils.probe_utils import is_debug_enabled, probe_external_agent
from app.utils.form_handlers import validate_external_agent_form, get_form_error_context

router = APIRouter(prefix="/external-agents", tags=["external-agents"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def list_external_agents_view(request: Request, session: Session = Depends(get_session)):
    """List external agents."""
    agents = list_external_agents(session)
    return templates.TemplateResponse(request, "external_agents/index.html", {
        "agents": agents,
        "debug_enabled": is_debug_enabled()
    })


@router.get("/new")
def new_external_agent_form(request: Request, session: Session = Depends(get_session)):
    """Show new external agent form."""
    return templates.TemplateResponse(request, "external_agents/form.html", {
        "errors": {}
    })


@router.post("/")
def create_external_agent_action(request: Request, session: Session = Depends(get_session),
                               name: str = Form(...), base_url: str = Form(...),
                               agent_type: str = Form(...), protocol: str = Form(...),
                               enabled: bool = Form(True)):
    """Create a new external agent."""
    try:
        validate_external_agent_form(name, base_url, agent_type, protocol)
        agent = create_external_agent(session, name, base_url, enabled, agent_type, protocol)
        return RedirectResponse(url="/external-agents", status_code=302)
        
    except Exception as e:
        return templates.TemplateResponse(request, "external_agents/form.html", {
            "errors": {"form": str(e)},
            **get_form_error_context(name, base_url, agent_type, protocol, enabled)
        })


@router.get("/{agent_id}/edit")
def edit_external_agent_form(request: Request, agent_id: int, session: Session = Depends(get_session)):
    """Show edit external agent form."""
    agent = get_external_agent_by_id(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="External agent not found")
    
    return templates.TemplateResponse(request, "external_agents/form.html", {
        "agent": agent,
        "errors": {}
    })


@router.post("/{agent_id}/edit")
def update_external_agent_action(request: Request, agent_id: int, session: Session = Depends(get_session),
                               name: str = Form(...), base_url: str = Form(...),
                               agent_type: str = Form(...), protocol: str = Form(...),
                               enabled: bool = Form(True)):
    """Update an external agent."""
    try:
        validate_external_agent_form(name, base_url, agent_type, protocol)
        agent = update_external_agent(session, agent_id, name, base_url, enabled, agent_type, protocol)
        if not agent:
            raise HTTPException(status_code=404, detail="External agent not found")
        
        return RedirectResponse(url="/external-agents", status_code=302)
        
    except Exception as e:
        agent = get_external_agent_by_id(session, agent_id)
        return templates.TemplateResponse(request, "external_agents/form.html", {
            "agent": agent,
            "errors": {"form": str(e)},
            **get_form_error_context(name, base_url, agent_type, protocol, enabled)
        })


@router.post("/{agent_id}/delete")
def delete_external_agent_action(agent_id: int, session: Session = Depends(get_session)):
    """Delete an external agent."""
    success = delete_external_agent(session, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="External agent not found")
    return RedirectResponse(url="/external-agents", status_code=302)


@router.get("/prefill-signals")
def prefill_signals_agent(request: Request):
    """Prefill form with default values for Audience Signals (3P)."""
    return templates.TemplateResponse(request, "external_agents/form.html", {
        "name": "Audience Signals (3P)",
        "base_url": "https://signals.example.com/api",
        "agent_type": "signals",
        "protocol": "rest",
        "enabled": True,
        "errors": {}
    })


@router.post("/{agent_id}/probe")
async def probe_external_agent_action(request: Request, agent_id: int, session: Session = Depends(get_session)):
    """Probe external agent connectivity (DEBUG only)."""
    if not is_debug_enabled():
        raise HTTPException(status_code=403, detail="Probe not available")
    
    agent = get_external_agent_by_id(session, agent_id)
    if not agent or not agent.enabled:
        raise HTTPException(status_code=404, detail="Agent not found or disabled")
    
    category, message = await probe_external_agent(agent.agent_type, agent.protocol, agent.base_url, agent.name)
    
    # Re-fetch agents for re-render
    agents = list_external_agents(session)
    
    return templates.TemplateResponse(request, "external_agents/index.html", {
        "agents": agents,
        "debug_enabled": True,
        "probe_results": {agent_id: {"category": category, "message": message}}
    })
