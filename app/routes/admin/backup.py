"""
Admin routes for backup and restore operations.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from app.utils.data_persistence import (
    create_backup, restore_backup, list_backups,
    export_all_data, import_all_data
)
from app.db import get_session

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/admin/backup", tags=["admin"])


@router.post("/create")
async def create_backup_endpoint():
    """Create a backup of all application data."""
    try:
        result = create_backup()
        return {"message": result, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.post("/restore")
async def restore_backup_endpoint(backup_file: Optional[str] = None):
    """Restore data from backup."""
    try:
        result = restore_backup(backup_file)
        return {"message": result, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.get("/list")
async def list_backups_endpoint():
    """List all available backup files."""
    try:
        backups = list_backups()
        return {"backups": backups, "count": len(backups)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.get("/export")
async def export_data_endpoint():
    """Export current data as JSON."""
    try:
        session = next(get_session())
        try:
            data = export_all_data(session)
            return {
                "message": "Data exported successfully",
                "data": data,
                "status": "success"
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/import")
async def import_data_endpoint(backup_file: Optional[str] = None):
    """Import data from backup file."""
    try:
        session = next(get_session())
        try:
            data = import_all_data(session, backup_file)
            return {
                "message": "Data imported successfully",
                "status": "success"
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/status")
async def backup_status_endpoint():
    """Get backup system status."""
    try:
        from app.utils.data_persistence import BACKUP_DIR
        import os
        
        backup_files = list(BACKUP_DIR.glob("full_backup_*.json"))
        latest_backup = None
        if backup_files:
            latest_backup = max(backup_files, key=os.path.getctime)
        
        return {
            "backup_directory": str(BACKUP_DIR),
            "total_backups": len(backup_files),
            "latest_backup": latest_backup.name if latest_backup else None,
            "latest_backup_time": latest_backup.stat().st_mtime if latest_backup else None,
            "status": "healthy"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/", response_class=HTMLResponse)
async def backup_admin_page(request: Request):
    """Serve the backup admin interface."""
    return templates.TemplateResponse("admin/backup.html", {"request": request})
