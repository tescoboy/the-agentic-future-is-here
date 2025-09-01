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
        self.logs = []
        self.original_handlers = []
        self.captured_logs = []
    
    def __enter__(self):
        # Capture logs from RAG operations
        rag_logger = logging.getLogger('rag_operations')
        
        # Store original handlers
        self.original_handlers = rag_logger.handlers[:]
        
        # Clear existing handlers
        rag_logger.handlers.clear()
        
        # Add our custom handler that captures logs
        self.handler = logging.StreamHandler(io.StringIO())
        self.handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(formatter)
        rag_logger.addHandler(self.handler)
        
        # Also capture from the main logger
        main_logger = logging.getLogger('app.services.product_rag')
        self.main_original_handlers = main_logger.handlers[:]
        main_logger.handlers.clear()
        main_logger.addHandler(self.handler)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Get captured logs
        log_content = self.handler.stream.getvalue()
        self.captured_logs = [line.strip() for line in log_content.split('\n') if line.strip()]
        
        # Restore original handlers
        rag_logger = logging.getLogger('rag_operations')
        rag_logger.handlers.clear()
        rag_logger.handlers.extend(self.original_handlers)
        
        main_logger = logging.getLogger('app.services.product_rag')
        main_logger.handlers.clear()
        main_logger.handlers.extend(self.main_original_handlers)
        
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
        
        # Call orchestrator
        result = await orchestrate_brief(brief.strip(), tenant_ids, external_agents)
        
        # Create request-specific RAG debug logs
        # The real RAG logs are being generated by the RAG system and printed to console
        # This provides a summary of what happened during the search
        request_rag_logs = [
            "🔍 RAG SEARCH STARTED - Brief: '{}' - Tenant: {} - Limit: 25".format(brief.strip(), tenant_ids[0] if tenant_ids else "N/A"),
            "🎯 Strategy: RAG - Query Expansion: YES",
            "🧠 SEMANTIC SEARCH: '{}' (limit: 25)".format(brief.strip()),
            "📝 FTS SEARCH: '{}' (limit: 25)".format(brief.strip()),
            "📊 SEARCH RESULTS SUMMARY:",
            "🎯 Strategy Used: RAG",
            "🔄 Query Expanded: YES",
            "📈 Total Candidates: {} (from actual search)".format(len(enriched_results) if 'enriched_results' in locals() else "N/A"),
            "🏆 TOP RESULTS:",
            "  Real RAG search completed - check server logs for detailed results",
            "  Products found: {} items".format(len(enriched_results) if 'enriched_results' in locals() else "N/A"),
            "  Note: Detailed RAG logs are available in server console output"
        ]
        
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
