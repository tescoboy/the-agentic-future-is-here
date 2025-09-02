"""
Admin routes for backup and restore operations.
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
import json
import tempfile
import os
from app.utils.data_persistence import (
    create_backup, restore_backup, list_backups,
    export_all_data, import_all_data
)
from app.utils.data_persistence.backup import test_persistent_disk
from app.utils.csv_backup import (
    export_to_csv_zip, import_from_csv_zip, list_csv_backups
)
from app.utils.data_persistence import BACKUP_DIR
from app.db import get_session
from app.services.embeddings_backfill import backfill_once

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
            
            # Calculate summary for user feedback
            total_tenants = len(data.get('tenants', []))
            total_products = sum(len(t.get('products', [])) for t in data.get('tenants', []))
            total_agents = len(data.get('external_agents', []))
            
            return {
                "message": f"Data exported successfully: {total_tenants} tenants, {total_products} products, {total_agents} agents",
                "data": data,
                "status": "success",
                "summary": {
                    "tenants": total_tenants,
                    "products": total_products,
                    "agents": total_agents,
                    "exported_at": data.get('exported_at')
                }
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/import")
async def import_data_endpoint(file: UploadFile = File(...)):
    """Import data from uploaded backup file."""
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are supported")
        
        # Read and parse the uploaded file
        content = await file.read()
        try:
            data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")
        
        # Import the data
        session = next(get_session())
        try:
            result = import_all_data(session, data)
            return {
                "message": "Data imported successfully",
                "status": "success",
                "details": result
            }
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/status")
async def backup_status_endpoint():
    """Get backup system status."""
    try:
        from app.utils.data_persistence import BACKUP_DIR
        import os
        
        # Include both compressed (.json.gz) and uncompressed (.json) backup files
        json_files = list(BACKUP_DIR.glob("full_backup_*.json"))
        gz_files = list(BACKUP_DIR.glob("full_backup_*.json.gz"))
        backup_files = json_files + gz_files
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


@router.post("/export-csv")
async def export_csv_backup_endpoint():
    """Export all data as CSV files in a zip archive."""
    try:
        session = next(get_session())
        try:
            zip_path = export_to_csv_zip(session)
            return {
                "message": "CSV backup created successfully",
                "file_path": zip_path,
                "status": "success"
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV export failed: {str(e)}")


@router.post("/import-csv")
async def import_csv_backup_endpoint(file: UploadFile = File(...)):
    """Import data from uploaded CSV zip file."""
    try:
        # Validate file type
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")
        
        # Save uploaded file temporarily
        temp_file = BACKUP_DIR / f"temp_import_{file.filename}"
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)
        
        try:
            # Import the data
            session = next(get_session())
            try:
                result = import_from_csv_zip(session, str(temp_file))
                return {
                    "message": "CSV data imported successfully",
                    "status": "success",
                    "details": result
                }
            finally:
                session.close()
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV import failed: {str(e)}")


@router.get("/list-csv")
async def list_csv_backups_endpoint():
    """List all available CSV backup files."""
    try:
        backups = list_csv_backups()
        return {"backups": backups, "count": len(backups)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list CSV backups: {str(e)}")


@router.get("/download-csv/{filename}")
async def download_csv_backup_endpoint(filename: str):
    """Download a specific CSV backup file."""
    try:
        from fastapi.responses import FileResponse
        file_path = BACKUP_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/zip'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/test-disk")
async def test_disk_endpoint():
    """Test if the persistent disk is working."""
    try:
        result = test_persistent_disk()
        return {"message": result, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disk test failed: {str(e)}")


@router.post("/backfill-embeddings")
async def backfill_embeddings_endpoint():
    """Trigger embeddings backfill for products."""
    try:
        session = next(get_session())
        try:
            result = await backfill_once(session, batch_size=32)
            return {
                "message": f"Embeddings backfill completed: {result['processed']} processed, {result['successful']} successful, {result['failed']} failed",
                "result": result,
                "status": "success"
            }
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embeddings backfill failed: {str(e)}")


@router.get("/", response_class=HTMLResponse)
async def backup_admin_page(request: Request):
    """Serve the backup admin interface."""
    return templates.TemplateResponse("admin/backup.html", {"request": request})
