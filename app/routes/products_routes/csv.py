"""Product CSV operations."""

from fastapi import APIRouter, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db import get_session
from app.repos.products import bulk_delete_products
from app.utils.csv_utils import generate_csv_template, parse_csv_file, import_products_from_csv

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/bulk-delete")
def bulk_delete_products_action(request: Request, session: Session = Depends(get_session),
                              product_ids: str = Form(...)):
    """Bulk delete products."""
    try:
        # Parse product IDs from form
        ids = [int(id.strip()) for id in product_ids.split(",") if id.strip()]
        deleted_count = bulk_delete_products(session, ids)
        return RedirectResponse(url="/products", status_code=302)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/csv-template")
def download_csv_template():
    """Download CSV template."""
    csv_content = generate_csv_template()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products_template.csv"}
    )


@router.get("/import")
def import_products_form(request: Request):
    """Show CSV import form."""
    return templates.TemplateResponse("products/import_result.html", {"request": request, "show_form": True})


@router.post("/import")
def import_products_action(request: Request, session: Session = Depends(get_session),
                          file: UploadFile = File(...)):
    """Import products from CSV."""
    # Validate file type
    if not file.content_type in ["text/csv", "application/vnd.ms-excel"]:
        return templates.TemplateResponse("products/import_result.html", {
            "request": request,
            "show_form": False,
            "import_result": {
                "error": f"Invalid file type. Expected CSV, got {file.content_type}"
            }
        })
    
    # Validate file size (5MB limit)
    if file.size and file.size > 5 * 1024 * 1024:
        return templates.TemplateResponse("products/import_result.html", {
            "request": request,
            "show_form": False,
            "import_result": {
                "error": "File too large. Maximum size is 5MB."
            }
        })
    
    try:
        # Read file content
        content = file.file.read()
        
        # Parse CSV
        valid_rows, invalid_rows, parse_errors = parse_csv_file(content)
        
        # Import valid rows
        imported_count, import_errors = import_products_from_csv(session, valid_rows)
        
        # Combine all errors
        all_errors = parse_errors + import_errors
        
        return templates.TemplateResponse("products/import_result.html", {
            "request": request,
            "show_form": False,
            "import_result": {
                "total_rows": len(valid_rows) + len(invalid_rows),
                "imported_count": imported_count,
                "invalid_count": len(invalid_rows) + len(all_errors),
                "errors": all_errors
            }
        })
        
    except Exception as e:
        return templates.TemplateResponse("products/import_result.html", {
            "request": request,
            "show_form": False,
            "import_result": {
                "error": f"Import failed: {str(e)}"
            }
        })
