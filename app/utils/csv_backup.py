"""
CSV backup utilities for exporting and importing application data.
Handles tenants, products, external agents, and prompts as separate CSV files in a zip archive.
"""

import csv
import json
import zipfile
import tempfile
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlmodel import Session, select
from pathlib import Path

from app.models import Tenant, Product, ExternalAgent
from app.utils.data_persistence import BACKUP_DIR

logger = logging.getLogger(__name__)


def export_to_csv_zip(session: Session) -> str:
    """
    Export all application data to CSV files and create a zip archive.
    
    Returns:
        str: Path to the created zip file
    """
    logger.info("Starting CSV export...")
    
    # Create temporary directory for CSV files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Export each table to CSV
        csv_files = {}
        
        # Export tenants
        tenants = session.exec(select(Tenant)).all()
        if tenants:
            csv_files['tenants'] = _export_tenants_to_csv(tenants, temp_path)
            logger.info(f"Exported {len(tenants)} tenants to CSV")
        
        # Export products
        products = session.exec(select(Product)).all()
        if products:
            csv_files['products'] = _export_products_to_csv(products, temp_path)
            logger.info(f"Exported {len(products)} products to CSV")
        
        # Export external agents
        agents = session.exec(select(ExternalAgent)).all()
        if agents:
            csv_files['external_agents'] = _export_agents_to_csv(agents, temp_path)
            logger.info(f"Exported {len(agents)} external agents to CSV")
        
        # Create zip file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"backup_csv_{timestamp}.zip"
        zip_path = BACKUP_DIR / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for table_name, csv_file in csv_files.items():
                zipf.write(csv_file, f"{table_name}.csv")
        
        logger.info(f"Created CSV backup: {zip_path}")
        return str(zip_path)


def import_from_csv_zip(session: Session, zip_path: str) -> Dict[str, Any]:
    """
    Import data from CSV files in a zip archive.
    
    Args:
        session: Database session
        zip_path: Path to the zip file
        
    Returns:
        Dict with import results
    """
    logger.info(f"Starting CSV import from: {zip_path}")
    
    results = {
        'tenants_imported': 0,
        'products_imported': 0,
        'agents_imported': 0,
        'errors': []
    }
    
    # Clear existing data
    products = session.exec(select(Product)).all()
    for product in products:
        session.delete(product)
    
    agents = session.exec(select(ExternalAgent)).all()
    for agent in agents:
        session.delete(agent)
    
    tenants = session.exec(select(Tenant)).all()
    for tenant in tenants:
        session.delete(tenant)
    
    session.commit()
    logger.info("Cleared existing data")
    
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        # Import tenants first (products depend on them)
        if 'tenants.csv' in zipf.namelist():
            try:
                with zipf.open('tenants.csv') as csv_file:
                    # Decode bytes to text
                    csv_text = csv_file.read().decode('utf-8')
                    tenants_imported = _import_tenants_from_csv_text(session, csv_text)
                    results['tenants_imported'] = tenants_imported
                    logger.info(f"Imported {tenants_imported} tenants")
            except Exception as e:
                error_msg = f"Error importing tenants: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Import products
        if 'products.csv' in zipf.namelist():
            try:
                with zipf.open('products.csv') as csv_file:
                    # Decode bytes to text
                    csv_text = csv_file.read().decode('utf-8')
                    products_imported = _import_products_from_csv_text(session, csv_text)
                    results['products_imported'] = products_imported
                    logger.info(f"Imported {products_imported} products")
            except Exception as e:
                error_msg = f"Error importing products: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Import external agents
        if 'external_agents.csv' in zipf.namelist():
            try:
                with zipf.open('external_agents.csv') as csv_file:
                    # Decode bytes to text
                    csv_text = csv_file.read().decode('utf-8')
                    agents_imported = _import_agents_from_csv_text(session, csv_text)
                    results['agents_imported'] = agents_imported
                    logger.info(f"Imported {agents_imported} external agents")
            except Exception as e:
                error_msg = f"Error importing external agents: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
    
    session.commit()
    logger.info("CSV import completed")
    return results


def _export_tenants_to_csv(tenants: List[Tenant], temp_path: Path) -> Path:
    """Export tenants to CSV file."""
    csv_file = temp_path / "tenants.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['id', 'name', 'slug', 'custom_prompt', 'enable_web_context', 'created_at'])
        
        # Write data
        for tenant in tenants:
            writer.writerow([
                tenant.id,
                tenant.name,
                tenant.slug,
                tenant.custom_prompt or '',
                tenant.enable_web_context,
                tenant.created_at.isoformat() if tenant.created_at else ''
            ])
    
    return csv_file


def _export_products_to_csv(products: List[Product], temp_path: Path) -> Path:
    """Export products to CSV file."""
    csv_file = temp_path / "products.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['id', 'tenant_id', 'name', 'description', 'price_cpm', 'delivery_type', 'formats_json', 'targeting_json', 'created_at'])
        
        # Write data
        for product in products:
            writer.writerow([
                product.id,
                product.tenant_id,
                product.name,
                product.description or '',
                product.price_cpm,
                product.delivery_type,
                product.formats_json or '',
                product.targeting_json or '',
                product.created_at.isoformat() if product.created_at else ''
            ])
    
    return csv_file


def _export_agents_to_csv(agents: List[ExternalAgent], temp_path: Path) -> Path:
    """Export external agents to CSV file."""
    csv_file = temp_path / "external_agents.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['id', 'name', 'base_url', 'enabled', 'agent_type', 'protocol', 'created_at'])
        
        # Write data
        for agent in agents:
            writer.writerow([
                agent.id,
                agent.name,
                agent.base_url,
                agent.enabled,
                agent.agent_type,
                agent.protocol,
                agent.created_at.isoformat() if agent.created_at else ''
            ])
    
    return csv_file


def _import_tenants_from_csv_text(session: Session, csv_text: str) -> int:
    """Import tenants from CSV text."""
    imported = 0
    
    # Create tenant lookup for products
    tenant_lookup = {}
    
    from io import StringIO
    reader = csv.DictReader(StringIO(csv_text))
    for row in reader:
        try:
            tenant = Tenant(
                id=int(row['id']) if row['id'] else None,
                name=row['name'],
                slug=row['slug'],
                custom_prompt=row['custom_prompt'] if row['custom_prompt'] else None,
                enable_web_context=row['enable_web_context'].lower() == 'true',
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            
            session.add(tenant)
            session.flush()  # Get the ID
            
            # Store for product lookup
            tenant_lookup[int(row['id'])] = tenant.id
            imported += 1
            
        except Exception as e:
            logger.error(f"Error importing tenant {row.get('name', 'unknown')}: {str(e)}")
    
    session.commit()
    return imported


def _import_tenants_from_csv(session: Session, csv_file) -> int:
    """Import tenants from CSV file."""
    imported = 0
    
    # Create tenant lookup for products
    tenant_lookup = {}
    
    reader = csv.DictReader(csv_file)
    for row in reader:
        try:
            tenant = Tenant(
                id=int(row['id']) if row['id'] else None,
                name=row['name'],
                slug=row['slug'],
                custom_prompt=row['custom_prompt'] if row['custom_prompt'] else None,
                enable_web_context=row['enable_web_context'].lower() == 'true',
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            
            session.add(tenant)
            session.flush()  # Get the ID
            
            # Store for product lookup
            tenant_lookup[int(row['id'])] = tenant.id
            imported += 1
            
        except Exception as e:
            logger.error(f"Error importing tenant {row.get('name', 'unknown')}: {str(e)}")
    
    session.commit()
    return imported


def _import_products_from_csv_text(session: Session, csv_text: str) -> int:
    """Import products from CSV text."""
    imported = 0
    
    from io import StringIO
    reader = csv.DictReader(StringIO(csv_text))
    for row in reader:
        try:
            product = Product(
                id=int(row['id']) if row['id'] else None,
                tenant_id=int(row['tenant_id']) if row['tenant_id'] else None,
                name=row['name'],
                description=row['description'] if row['description'] else None,
                price_cpm=float(row['price_cpm']) if row['price_cpm'] else 0.0,
                delivery_type=row['delivery_type'],
                formats_json=row['formats_json'] if row['formats_json'] else None,
                targeting_json=row['targeting_json'] if row['targeting_json'] else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            
            session.add(product)
            imported += 1
            
        except Exception as e:
            logger.error(f"Error importing product {row.get('name', 'unknown')}: {str(e)}")
    
    session.commit()
    return imported


def _import_products_from_csv(session: Session, csv_file) -> int:
    """Import products from CSV file."""
    imported = 0
    
    reader = csv.DictReader(csv_file)
    for row in reader:
        try:
            product = Product(
                id=int(row['id']) if row['id'] else None,
                tenant_id=int(row['tenant_id']) if row['tenant_id'] else None,
                name=row['name'],
                description=row['description'] if row['description'] else None,
                price_cpm=float(row['price_cpm']) if row['price_cpm'] else 0.0,
                delivery_type=row['delivery_type'],
                formats_json=row['formats_json'] if row['formats_json'] else None,
                targeting_json=row['targeting_json'] if row['targeting_json'] else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            
            session.add(product)
            imported += 1
            
        except Exception as e:
            logger.error(f"Error importing product {row.get('name', 'unknown')}: {str(e)}")
    
    session.commit()
    return imported


def _import_agents_from_csv_text(session: Session, csv_text: str) -> int:
    """Import external agents from CSV text."""
    imported = 0
    
    from io import StringIO
    reader = csv.DictReader(StringIO(csv_text))
    for row in reader:
        try:
            agent = ExternalAgent(
                id=int(row['id']) if row['id'] else None,
                name=row['name'],
                base_url=row['base_url'],
                enabled=row['enabled'].lower() == 'true',
                agent_type=row['agent_type'],
                protocol=row['protocol'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            
            session.add(agent)
            imported += 1
            
        except Exception as e:
            logger.error(f"Error importing agent {row.get('name', 'unknown')}: {str(e)}")
    
    session.commit()
    return imported


def _import_agents_from_csv(session: Session, csv_file) -> int:
    """Import external agents from CSV file."""
    imported = 0
    
    reader = csv.DictReader(csv_file)
    for row in reader:
        try:
            agent = ExternalAgent(
                id=int(row['id']) if row['id'] else None,
                name=row['name'],
                base_url=row['base_url'],
                enabled=row['enabled'].lower() == 'true',
                agent_type=row['agent_type'],
                protocol=row['protocol'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            
            session.add(agent)
            imported += 1
            
        except Exception as e:
            logger.error(f"Error importing agent {row.get('name', 'unknown')}: {str(e)}")
    
    session.commit()
    return imported


def list_csv_backups() -> List[str]:
    """List all available CSV backup files."""
    csv_backups = []
    for file in BACKUP_DIR.glob("backup_csv_*.zip"):
        csv_backups.append(file.name)
    return sorted(csv_backups, reverse=True)
