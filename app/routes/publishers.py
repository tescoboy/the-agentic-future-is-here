"""Publishers index route for listing all publishers."""

import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlmodel import Session

from app.db import get_session
from app.repos.tenants import list_tenants
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/publishers", tags=["publishers"])
templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


@router.get("/", response_class=HTMLResponse)
def publishers_index(request: Request, session: Session = Depends(get_session)):
    """List all publishers with links to their portals."""
    tenants, total = list_tenants(session)
    
    return templates.TemplateResponse("publishers/index.html", {
        "request": request,
        "tenants": tenants,
        "total": total
    })
