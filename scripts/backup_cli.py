#!/usr/bin/env python3
"""
CLI interface for optimized backup and restore operations.
Provides easy-to-use commands for comprehensive data management.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, ensure_database
from app.utils.data_persistence.optimized_backup import (
    OptimizedBackupManager,
    create_optimized_backup,
    restore_optimized_backup,
    validate_backup_file
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backup_operations.log')
    ]
)

logger = logging.getLogger(__name__)


async def cmd_create_backup(args):
    """Create a comprehensive backup."""
    logger.info("🚀 Starting backup creation...")
    
    try:
        ensure_database()
        session = next(get_session())
        
        try:
            manager = OptimizedBackupManager(session)
            backup_data = await manager.create_comprehensive_backup(
                use_compression=args.compress
            )
            
            print("✅ Backup created successfully!")
            print(f"📊 Statistics:")
            metadata = backup_data.get("backup_metadata", {})
            data_counts = metadata.get("data_counts", {})
            
            for key, count in data_counts.items():
                print(f"  - {key.replace('_', ' ').title()}: {count}")
            
            if args.output:
                print(f"📁 Backup location: {args.output}")
            
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        print(f"❌ Backup failed: {e}")
        sys.exit(1)


async def cmd_restore_backup(args):
    """Restore from a backup file."""
    logger.info(f"🔄 Starting backup restore from: {args.backup_file}")
    
    try:
        ensure_database()
        session = next(get_session())
        
        try:
            if args.validate_only:
                # Just validate without restoring
                validation_result = await validate_backup_file(args.backup_file)
                
                if validation_result["valid"]:
                    print("✅ Backup file is valid!")
                    if validation_result["warnings"]:
                        print("⚠️ Warnings:")
                        for warning in validation_result["warnings"]:
                            print(f"  - {warning}")
                else:
                    print("❌ Backup file validation failed!")
                    for error in validation_result["errors"]:
                        print(f"  - {error}")
                    sys.exit(1)
            else:
                # Confirm restore if not forced
                if not args.force:
                    response = input("⚠️ This will replace all existing data. Continue? (yes/no): ")
                    if response.lower() not in ['yes', 'y']:
                        print("❌ Restore cancelled")
                        return
                
                manager = OptimizedBackupManager(session)
                result = await manager.restore_comprehensive_backup(
                    backup_file=args.backup_file,
                    validate_before_restore=not args.skip_validation
                )
                
                print("✅ Restore completed successfully!")
                print("📊 Validation Results:")
                for key, value in result.items():
                    if key != "validation_timestamp":
                        print(f"  - {key.replace('_', ' ').title()}: {value}")
        
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        print(f"❌ Restore failed: {e}")
        sys.exit(1)


async def cmd_list_backups(args):
    """List available backup files."""
    from app.utils.data_persistence.core import BACKUP_DIR
    
    print("📂 Available backup files:")
    
    # List comprehensive backups
    comprehensive_backups = sorted(
        BACKUP_DIR.glob("comprehensive_backup_*.json*"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if comprehensive_backups:
        print("\n🔥 Optimized Comprehensive Backups:")
        for backup in comprehensive_backups[:args.limit]:
            size_mb = backup.stat().st_size / (1024 * 1024)
            mod_time = backup.stat().st_mtime
            import datetime
            mod_date = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"  📄 {backup.name}")
            print(f"      Size: {size_mb:.2f} MB")
            print(f"      Modified: {mod_date}")
            print()
    
    # List legacy backups
    legacy_backups = sorted(
        BACKUP_DIR.glob("full_backup_*.json*"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if legacy_backups:
        print("📋 Legacy Backups:")
        for backup in legacy_backups[:args.limit]:
            size_mb = backup.stat().st_size / (1024 * 1024)
            mod_time = backup.stat().st_mtime
            import datetime
            mod_date = datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"  📄 {backup.name}")
            print(f"      Size: {size_mb:.2f} MB")
            print(f"      Modified: {mod_date}")
    
    if not comprehensive_backups and not legacy_backups:
        print("  No backup files found.")


async def cmd_validate_backup(args):
    """Validate a backup file."""
    print(f"🔍 Validating backup file: {args.backup_file}")
    
    try:
        validation_result = await validate_backup_file(args.backup_file)
        
        if validation_result["valid"]:
            print("✅ Backup file is valid!")
            
            if validation_result["warnings"]:
                print("\n⚠️ Warnings found:")
                for warning in validation_result["warnings"]:
                    print(f"  - {warning}")
        else:
            print("❌ Backup file validation failed!")
            print("\n🚨 Errors found:")
            for error in validation_result["errors"]:
                print(f"  - {error}")
            
            if validation_result["warnings"]:
                print("\n⚠️ Warnings:")
                for warning in validation_result["warnings"]:
                    print(f"  - {warning}")
            
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"❌ Validation failed: {e}")
        sys.exit(1)


async def cmd_info(args):
    """Show backup system information."""
    from app.utils.data_persistence.core import BACKUP_DIR, DATA_DIR
    
    print("ℹ️ Backup System Information")
    print("=" * 50)
    
    print(f"📁 Data Directory: {DATA_DIR.absolute()}")
    print(f"📁 Backup Directory: {BACKUP_DIR.absolute()}")
    print(f"🗄️ Database URL: {Path('./data/adcp_demo.sqlite3').absolute()}")
    
    # Check database
    try:
        ensure_database()
        session = next(get_session())
        
        try:
            from sqlmodel import text
            
            # Count records
            tenant_count = session.execute(text("SELECT COUNT(*) FROM tenant")).scalar()
            product_count = session.execute(text("SELECT COUNT(*) FROM product")).scalar()
            agent_count = session.execute(text("SELECT COUNT(*) FROM externalagent")).scalar()
            
            try:
                embedding_count = session.execute(text("SELECT COUNT(*) FROM product_embeddings")).scalar()
            except:
                embedding_count = 0
            
            print(f"\n📊 Current Database Contents:")
            print(f"  - Tenants: {tenant_count}")
            print(f"  - Products: {product_count}")
            print(f"  - External Agents: {agent_count}")
            print(f"  - Embeddings: {embedding_count}")
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
    
    # Backup directory info
    if BACKUP_DIR.exists():
        backup_files = list(BACKUP_DIR.glob("*.json*"))
        total_size = sum(f.stat().st_size for f in backup_files) / (1024 * 1024)
        
        print(f"\n💾 Backup Storage:")
        print(f"  - Total backup files: {len(backup_files)}")
        print(f"  - Total size: {total_size:.2f} MB")
    else:
        print(f"\n💾 Backup directory does not exist yet")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Optimized backup and restore CLI for AdCP Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a compressed backup
  python backup_cli.py create --compress
  
  # Restore from a specific backup
  python backup_cli.py restore backup_file.json.gz
  
  # List recent backups
  python backup_cli.py list --limit 5
  
  # Validate a backup before restoring
  python backup_cli.py validate backup_file.json.gz
  
  # Show system information
  python backup_cli.py info
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create backup
    create_parser = subparsers.add_parser('create', help='Create a comprehensive backup')
    create_parser.add_argument('--compress', action='store_true', 
                             help='Compress the backup file (recommended)')
    create_parser.add_argument('--output', '-o', 
                             help='Output file path (optional)')
    create_parser.set_defaults(func=cmd_create_backup)
    
    # Restore backup
    restore_parser = subparsers.add_parser('restore', help='Restore from a backup file')
    restore_parser.add_argument('backup_file', help='Path to backup file')
    restore_parser.add_argument('--force', '-f', action='store_true',
                              help='Skip confirmation prompt')
    restore_parser.add_argument('--skip-validation', action='store_true',
                              help='Skip backup validation before restore')
    restore_parser.add_argument('--validate-only', action='store_true',
                              help='Only validate, do not restore')
    restore_parser.set_defaults(func=cmd_restore_backup)
    
    # List backups
    list_parser = subparsers.add_parser('list', help='List available backup files')
    list_parser.add_argument('--limit', '-n', type=int, default=10,
                           help='Maximum number of files to show (default: 10)')
    list_parser.set_defaults(func=cmd_list_backups)
    
    # Validate backup
    validate_parser = subparsers.add_parser('validate', help='Validate a backup file')
    validate_parser.add_argument('backup_file', help='Path to backup file')
    validate_parser.set_defaults(func=cmd_validate_backup)
    
    # Info
    info_parser = subparsers.add_parser('info', help='Show backup system information')
    info_parser.set_defaults(func=cmd_info)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run the appropriate command
    try:
        asyncio.run(args.func(args))
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"❌ Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()