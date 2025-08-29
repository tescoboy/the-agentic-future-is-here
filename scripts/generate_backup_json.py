#!/usr/bin/env python3
"""
Generate a JSON backup file from CSV data for upload via backup system.
"""

import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime

def generate_backup_json():
    """Generate a JSON backup file from catalog_final.csv."""
    
    # Find the CSV file
    possible_paths = [
        "./catalog_final.csv",
        "catalog_final.csv",
        "../catalog_final.csv",
        Path(__file__).parent.parent / "catalog_final.csv"
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        print(f"Error: CSV file not found in any of these locations: {possible_paths}")
        sys.exit(1)
    
    print(f"Found CSV file at: {csv_path}")
    
    # Tenant mapping
    tenant_names = {
        'tiktok': 'TikTok',
        'iheart-radio': 'iHeart Radio',
        'netflix': 'Netflix',
        'nytimes': 'New York Times'
    }
    
    # Initialize backup data structure
    backup_data = {
        "export_timestamp": datetime.now().isoformat(),
        "version": "1.0",
        "tenants": [],
        "products": [],
        "external_agents": [],
        "app_settings": {},
        "tenant_settings": {}
    }
    
    # Track tenants and their IDs
    tenants = {}
    tenant_id_counter = 1
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            tenant_slug = row['tenant_slug']
            
            # Skip rows with empty tenant slugs
            if not tenant_slug or not tenant_slug.strip():
                print(f"Warning: Skipping row with empty tenant_slug: {row.get('product_name', 'Unknown')}")
                continue
            
            # Create tenant if not already created
            if tenant_slug not in tenants:
                tenant_name = tenant_names.get(tenant_slug, tenant_slug.title())
                tenant_data = {
                    "id": tenant_id_counter,
                    "name": tenant_name,
                    "slug": tenant_slug,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                tenants[tenant_slug] = tenant_data
                backup_data["tenants"].append(tenant_data)
                tenant_id_counter += 1
            
            # Create product data
            product_data = {
                "id": len(backup_data["products"]) + 1,
                "tenant_id": tenants[tenant_slug]["id"],
                "name": row['product_name'],
                "description": row['description'],
                "price_cpm": float(row['price_cpm']),
                "delivery_type": row['delivery_type'],
                "formats_json": row['formats_json'],
                "targeting_json": row['targeting_json'],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            backup_data["products"].append(product_data)
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"csv_backup_{timestamp}.json"
    
    # Write JSON file
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(backup_data, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Generated backup file: {output_file}")
    print(f"Contains {len(backup_data['tenants'])} tenants and {len(backup_data['products'])} products")
    
    return output_file

if __name__ == "__main__":
    generate_backup_json()
