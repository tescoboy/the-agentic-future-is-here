"""Buyer UI routes for brief submission and results display."""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.db import get_session
from app.repos.tenants import list_tenants
from app.repos.external_agents import list_external_agents
from app.services.orchestrator import orchestrate_brief
import io
import sys
from app.utils.results import (
    parse_agent_selections, enrich_sales_results, filter_items_by_score_threshold,
    generate_heat_indicator, calculate_summary_stats
)
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/buyer", tags=["buyer"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)

# Global variable to capture RAG logs
rag_debug_logs = []

class RAGLogCapture:
    """Context manager to capture RAG logs."""
    def __init__(self):
        self.captured_logs = []
        self.log_buffer = []
    
    def __enter__(self):
        # Simple approach: create a custom log handler that saves all logs
        self.log_buffer = []
        
        # Create a custom handler that captures to our buffer
        class BufferHandler(logging.Handler):
            def __init__(self, buffer):
                super().__init__()
                self.buffer = buffer
                
            def emit(self, record):
                # Save the full log message
                self.buffer.append(self.format(record))
        
        # Set up the buffer handler
        self.buffer_handler = BufferHandler(self.log_buffer)
        self.buffer_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        self.buffer_handler.setFormatter(formatter)
        
        # Add to root logger to catch everything
        root_logger = logging.getLogger()
        root_logger.addHandler(self.buffer_handler)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Remove our handler from root logger
        root_logger = logging.getLogger()
        root_logger.removeHandler(self.buffer_handler)
        
        # Filter for relevant logs
        relevant_logs = []
        for log in self.log_buffer:
            if any(keyword in log for keyword in [
                'RAG', 'WEB_DEBUG', 'AI_DEBUG', 'snippet:', 'Strategy Used:', 
                'Total Candidates:', 'Expansion complete:', 'QUERY EXPANSION:',
                'Product', 'Raw response text:', 'Successfully parsed'
            ]):
                relevant_logs.append(log)
        
        self.captured_logs = relevant_logs
        global rag_debug_logs
        rag_debug_logs = self.captured_logs


def _get_available_agents(db_session: Session) -> List[Dict[str, Any]]:
    """Get all available agents for the buyer form."""
    agents = []
    
    # Add internal tenants (Sales agents)
    tenants, _ = list_tenants(db_session, "", 100, 0)
    for tenant in tenants:
        agents.append({
            "id": f"sales:tenant:{tenant.id}",
            "name": tenant.name,
            "type": "Sales",
            "enabled": True  # All tenants are considered enabled
        })
    
    # Add external agents
    external_agents = list_external_agents(db_session)
    for agent in external_agents:
        if agent.enabled:
            source = "external"
            agent_type = "Sales" if agent.agent_type == "sales" else "Signals"
            agents.append({
                "id": f"{agent.agent_type}:{source}:{agent.id}",
                "name": agent.name,
                "type": agent_type,
                "enabled": agent.enabled
            })
    
    return agents


@router.get("/", response_class=HTMLResponse)
async def buyer_form(
    request: Request,
    db_session: Session = Depends(get_session)
):
    """Display buyer form with agent selection."""
    agents = _get_available_agents(db_session)
    
    return templates.TemplateResponse(
        "buyer/index.html",
        {
            "request": request,
            "agents": agents,
            "brief": "",
            "selected_agents": [agent["id"] for agent in agents if agent["enabled"]],
            "errors": []
        }
    )


@router.post("/", response_class=HTMLResponse)
async def submit_brief(
    request: Request,
    brief: str = Form(...),
    agents: List[str] = Form(default=[]),
    db_session: Session = Depends(get_session)
):
    """Process brief submission and display results."""
    errors = []
    
    # Validate brief
    if not brief or not brief.strip():
        errors.append("Brief is required and cannot be empty")
    
    # Validate agent selection
    if not agents:
        errors.append("At least one agent must be selected")
    
    # If validation errors, re-render form with errors
    if errors:
        available_agents = _get_available_agents(db_session)
        return templates.TemplateResponse(
            "buyer/index.html",
            {
                "request": request,
                "agents": available_agents,
                "brief": brief,
                "selected_agents": agents,
                "errors": errors
            }
        )
    
    try:
        # Parse agent selections
        tenant_ids, external_agents = parse_agent_selections(agents, db_session)
        
        # Capture logs during orchestrator call
        with RAGLogCapture() as log_capture:
            # Call orchestrator
            result = await orchestrate_brief(brief.strip(), tenant_ids, external_agents)
        
        # Get captured logs
        request_rag_logs = log_capture.captured_logs
        

        
        # Enrich sales results with product data
        enriched_results = enrich_sales_results(result["results"], db_session)
        
        # Apply score threshold filtering
        for result_item in enriched_results:
            if result_item.get("ok") and result_item.get("items"):
                result_item["product_items"] = filter_items_by_score_threshold(result_item["items"])
        
        for signal_item in result["signals"]:
            if signal_item.get("ok") and signal_item.get("items"):
                signal_item["signal_items"] = filter_items_by_score_threshold(signal_item["items"])
        
        # Calculate summary statistics
        summary_stats = calculate_summary_stats(enriched_results, result["signals"])
        
        # Log submission metadata
        agent_count = len(agents)
        logger.info(f"Brief submitted: {agent_count} agents selected, {summary_stats['success']} succeeded, {summary_stats['failure']} failed")
        
        # Debug: Log the rag_debug_logs
        logger.info(f"RAG debug logs being passed to template: {len(request_rag_logs)} logs")
        
        template_context = {
            "request": request,
            "brief": brief.strip(),
            "sales_results": enriched_results,
            "signals": result["signals"],
            "summary_stats": summary_stats,
            "rag_debug_logs": request_rag_logs
        }
        return templates.TemplateResponse(
            "buyer/results.html",
            {
                **template_context,
                "generate_heat_indicator": generate_heat_indicator
            }
        )
        
    except ValueError as e:
        # Handle validation errors from agent parsing
        errors.append(f"Invalid agent selection: {str(e)}")
        available_agents = _get_available_agents(db_session)
        return templates.TemplateResponse(
            "buyer/index.html",
            {
                "request": request,
                "agents": available_agents,
                "brief": brief,
                "selected_agents": agents,
                "errors": errors
            }
        )
    except Exception as e:
        # Handle orchestrator or other errors
        logger.error(f"Error processing brief: {str(e)}")
        return templates.TemplateResponse(
            "buyer/results.html",
            {
                "request": request,
                "brief": brief.strip(),
                "sales_results": [],
                "signals": [],
                "summary_stats": {"success": 0, "failure": 0, "total": 0},
                "orchestrator_error": "An error occurred while processing your brief. Please try again.",
                "generate_heat_indicator": generate_heat_indicator
            }
        )


@router.get("/debug/rag-logs", response_class=JSONResponse)
async def get_rag_debug_logs():
    """Get the latest RAG debug logs."""
    return {"rag_logs": rag_debug_logs}



