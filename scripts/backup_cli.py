#!/usr/bin/env python3
"""
CLI script for backup and restore operations.
"""

import argparse
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.data_persistence import (
    create_backup, restore_backup, list_backups,
    export_all_data, import_all_data
)
from app.db import get_session


def main():
    parser = argparse.ArgumentParser(description="Backup and restore CLI tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create backup command
    create_parser = subparsers.add_parser("create", help="Create a backup")
    create_parser.add_argument("--description", "-d", help="Backup description")
    
    # Restore backup command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("--file", "-f", help="Backup file to restore from")
    
    # List backups command
    list_parser = subparsers.add_parser("list", help="List available backups")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export data to JSON")
    export_parser.add_argument("--output", "-o", help="Output file path")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import data from JSON")
    import_parser.add_argument("--file", "-f", required=True, help="JSON file to import")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show backup system status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "create":
            print("Creating backup...")
            result = create_backup()
            print(f"✅ {result}")
            
        elif args.command == "restore":
            if args.file:
                print(f"Restoring from {args.file}...")
                result = restore_backup(args.file)
            else:
                print("Restoring from latest backup...")
                result = restore_backup()
            print(f"✅ {result}")
            
        elif args.command == "list":
            backups = list_backups()
            if not backups:
                print("No backup files found.")
            else:
                print("Available backups:")
                for i, backup in enumerate(backups, 1):
                    print(f"  {i}. {backup}")
                    
        elif args.command == "export":
            print("Exporting data...")
            session = next(get_session())
            try:
                data = export_all_data(session)
                if args.output:
                    import json
                    with open(args.output, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"✅ Data exported to {args.output}")
                else:
                    print("✅ Data exported successfully")
            finally:
                session.close()
                
        elif args.command == "import":
            if not os.path.exists(args.file):
                print(f"❌ File not found: {args.file}")
                return
                
            print(f"Importing from {args.file}...")
            session = next(get_session())
            try:
                import_all_data(session, args.file)
                print("✅ Data imported successfully")
            finally:
                session.close()
                
        elif args.command == "status":
            from app.utils.data_persistence import BACKUP_DIR
            import os
            
            backup_files = list(BACKUP_DIR.glob("full_backup_*.json"))
            latest_backup = None
            if backup_files:
                latest_backup = max(backup_files, key=os.path.getctime)
            
            print("Backup System Status:")
            print(f"  Directory: {BACKUP_DIR}")
            print(f"  Total backups: {len(backup_files)}")
            print(f"  Latest backup: {latest_backup.name if latest_backup else 'None'}")
            print(f"  Status: {'Healthy' if BACKUP_DIR.exists() else 'Error'}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
