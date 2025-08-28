"""
CSV utilities for product import/export.
"""

import csv
import io
import json
import logging
from typing import List, Dict, Tuple, Any
from sqlmodel import Session
from app.repos.tenants import get_tenant_by_slug
from app.repos.products import create_product

logger = logging.getLogger(__name__)


def generate_csv_template() -> str:
    """Generate CSV template with headers."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        'tenant_slug', 'product_name', 'description', 'price_cpm', 
        'delivery_type', 'formats_json', 'targeting_json'
    ]
    writer.writerow(headers)
    
    return output.getvalue()


def validate_csv_row(row: Dict[str, str], row_num: int, require_tenant_slug: bool = True) -> Tuple[bool, str]:
    """Validate a single CSV row."""
    # Check required fields
    required_fields = ['product_name', 'price_cpm', 'delivery_type']
    if require_tenant_slug:
        required_fields.append('tenant_slug')
    
    for field in required_fields:
        if not row.get(field) or not row[field].strip():
            return False, f"Row {row_num}: Missing required field '{field}'"
    
    # Validate price_cpm
    try:
        price = float(row['price_cpm'])
        if price < 0:
            return False, f"Row {row_num}: price_cpm must be non-negative, got {price}"
    except ValueError:
        return False, f"Row {row_num}: Invalid price_cpm value '{row['price_cpm']}'"
    
    # Validate JSON fields
    json_fields = ['formats_json', 'targeting_json']
    for field in json_fields:
        value = row.get(field, '').strip()
        if value:  # Only validate if not empty
            try:
                json.loads(value)
            except json.JSONDecodeError:
                return False, f"Row {row_num}: Invalid JSON in '{field}': '{value[:50]}...'"
    
    return True, ""


def parse_csv_file(file_content: bytes, require_tenant_slug: bool = True) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[str]]:
    """Parse CSV file and separate valid/invalid rows."""
    try:
        # Decode as UTF-8
        content = file_content.decode('utf-8')
    except UnicodeDecodeError:
        return [], [], ["Error: File must be UTF-8 encoded"]
    
    try:
        reader = csv.DictReader(io.StringIO(content))
        valid_rows = []
        invalid_rows = []
        errors = []
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            is_valid, error_msg = validate_csv_row(row, row_num, require_tenant_slug)
            
            if is_valid:
                # Handle empty JSON fields
                if not row.get('formats_json', '').strip():
                    row['formats_json'] = '{}'
                if not row.get('targeting_json', '').strip():
                    row['targeting_json'] = '{}'
                valid_rows.append(row)
            else:
                invalid_rows.append(row)
                errors.append(error_msg)
        
        return valid_rows, invalid_rows, errors
        
    except Exception as e:
        return [], [], [f"Error parsing CSV file: {str(e)}"]


def import_products_from_csv(session: Session, valid_rows: List[Dict[str, str]], tenant_id: int = None) -> Tuple[int, List[str]]:
    """Import products from validated CSV rows."""
    imported_count = 0
    errors = []
    
    for row_num, row in enumerate(valid_rows, start=1):
        try:
            # Determine tenant_id
            if tenant_id is not None:
                # Use provided tenant_id (for publisher imports)
                target_tenant_id = tenant_id
            else:
                # Use tenant_slug from CSV (for admin imports)
                tenant = get_tenant_by_slug(session, row['tenant_slug'])
                if not tenant:
                    errors.append(f"Row {row_num + 1}: Tenant with slug '{row['tenant_slug']}' not found")
                    continue
                target_tenant_id = tenant.id
            
            # Create product
            create_product(
                session=session,
                tenant_id=target_tenant_id,
                name=row['product_name'],
                description=row.get('description', ''),
                price_cpm=float(row['price_cpm']),
                delivery_type=row['delivery_type'],
                formats_json=row['formats_json'],
                targeting_json=row['targeting_json']
            )
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Row {row_num + 1}: {str(e)}")
    
    logger.info(f"CSV import completed: {imported_count} imported, {len(errors)} errors")
    return imported_count, errors

