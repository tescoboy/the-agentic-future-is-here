# Optimized Backup System Documentation

## Overview

The AdCP Demo Optimized Backup System provides comprehensive, fast, and reliable backup and restore functionality for all application data and settings. This system is designed for production use with validation, error handling, and async operations for maximum performance.

## Features

### 🚀 **Comprehensive Data Coverage**
- **Database Tables**: All tables (tenants, products, external agents, embeddings)
- **Settings Files**: Application settings, tenant configurations
- **Database Schema**: Table structures, indexes, foreign keys
- **FTS Tables**: Full-text search tables and indexes
- **Environment Config**: Environment variables and feature flags
- **System Metadata**: Backup versioning and validation data

### ⚡ **Performance Optimized**
- **Bulk Operations**: Uses SQL bulk operations for speed
- **Compression**: Gzip compression reduces file sizes by ~97%
- **Async Operations**: Non-blocking file I/O operations
- **Efficient Memory Usage**: Streams large datasets

### 🔒 **Production Ready**
- **Data Validation**: Comprehensive integrity checks
- **Error Handling**: Graceful failure recovery
- **Transaction Safety**: Atomic operations where possible
- **Logging**: Detailed operation logging
- **CLI Interface**: Easy-to-use command line tools

## Quick Start

### Creating a Backup

```bash
# Activate virtual environment
source venv/bin/activate

# Create compressed backup (recommended)
python scripts/backup_cli.py create --compress

# Or create uncompressed backup
python scripts/backup_cli.py create
```

### Listing Backups

```bash
# List recent backups
python scripts/backup_cli.py list

# List specific number of backups
python scripts/backup_cli.py list --limit 5
```

### Validating a Backup

```bash
# Validate backup integrity
python scripts/backup_cli.py validate backup_file.json.gz
```

### Restoring from Backup

```bash
# Restore with confirmation prompt
python scripts/backup_cli.py restore backup_file.json.gz

# Force restore without confirmation
python scripts/backup_cli.py restore backup_file.json.gz --force

# Validate only (don't restore)
python scripts/backup_cli.py restore backup_file.json.gz --validate-only
```

### System Information

```bash
# Show backup system status
python scripts/backup_cli.py info
```

## CLI Reference

### Commands

| Command | Description | Options |
|---------|-------------|---------|
| `create` | Create comprehensive backup | `--compress`, `--output` |
| `restore` | Restore from backup | `--force`, `--skip-validation`, `--validate-only` |
| `list` | List available backups | `--limit N` |
| `validate` | Validate backup file | - |
| `info` | Show system information | - |

### Options

- `--compress`: Enable gzip compression (recommended)
- `--force`: Skip confirmation prompts
- `--skip-validation`: Skip backup validation before restore
- `--validate-only`: Only validate, don't restore
- `--limit N`: Limit number of files shown
- `--output PATH`: Specify output file path

## Programming Interface

### Creating Backups

```python
from app.db import get_session
from app.utils.data_persistence.optimized_backup import create_optimized_backup

session = next(get_session())
try:
    result = await create_optimized_backup(session, use_compression=True)
    print(result)
finally:
    session.close()
```

### Restoring Backups

```python
from app.db import get_session
from app.utils.data_persistence.optimized_backup import restore_optimized_backup

session = next(get_session())
try:
    result = await restore_optimized_backup(session, backup_file="backup.json.gz")
    print(result)
finally:
    session.close()
```

### Advanced Usage

```python
from app.utils.data_persistence.optimized_backup import OptimizedBackupManager

session = next(get_session())
manager = OptimizedBackupManager(session)

# Create backup
backup_data = await manager.create_comprehensive_backup(use_compression=True)

# Validate backup
validation_result = await manager._validate_backup_integrity(backup_data)

# Restore backup
result = await manager.restore_comprehensive_backup(
    backup_data=backup_data,
    validate_before_restore=True
)
```

## Backup File Structure

### Comprehensive Backup Format (v2.0)

```json
{
  "backup_metadata": {
    "created_at": "2025-09-02T17:46:46.629000",
    "version": "2.0",
    "backup_type": "comprehensive",
    "system_info": {
      "hostname": "server",
      "platform": "posix",
      "python_version": "3.10.0",
      "backup_tool_version": "2.0"
    },
    "data_counts": {
      "tenants": 6,
      "products": 1250,
      "external_agents": 1,
      "embeddings": 0
    }
  },
  "tenants": [...],
  "products": [...],
  "external_agents": [...],
  "product_embeddings": [...],
  "app_settings": {
    "environment_variables": {...},
    "file_settings": {...}
  },
  "tenant_settings": {...},
  "database_schema": {
    "tables": {...},
    "indexes": {...},
    "foreign_keys": {...}
  },
  "fts_tables": {...},
  "environment_config": {...},
  "feature_flags": {...}
}
```

## Data Validation

### Backup Integrity Checks

1. **Required Sections**: Ensures all essential data sections exist
2. **Relationship Validation**: Checks foreign key relationships
3. **Data Consistency**: Validates data types and formats
4. **Orphaned Records**: Identifies records with missing dependencies

### Restore Validation

1. **Pre-Restore**: Validates backup before starting restore
2. **Post-Restore**: Confirms data was restored correctly
3. **Count Verification**: Ensures record counts match backup
4. **Data Integrity**: Spot checks critical data relationships

## Performance Characteristics

### Backup Performance

| Dataset Size | Time | Compressed Size | Compression Ratio |
|--------------|------|-----------------|-------------------|
| 6 tenants, 1250 products | <1 second | 0.03 MB | ~97% |
| 100 tenants, 10K products | ~2 seconds | ~0.3 MB | ~97% |
| 1000 tenants, 100K products | ~10 seconds | ~3 MB | ~97% |

### Restore Performance

- **Small datasets** (< 10K records): 1-2 seconds
- **Medium datasets** (10K-100K records): 5-10 seconds  
- **Large datasets** (> 100K records): 10-30 seconds

Performance scales linearly with data size due to bulk operations.

## Error Handling

### Common Issues and Solutions

#### Backup Failures

```
Error: Session conflicts
Solution: Use sequential operations (already implemented)

Error: Disk space
Solution: Check available disk space before backup

Error: Permission denied
Solution: Ensure write permissions to backup directory
```

#### Restore Failures

```
Error: Foreign key constraint
Solution: Restore order is tenant → product → agents → embeddings

Error: Backup validation failed
Solution: Use --skip-validation flag or check backup integrity

Error: File not found
Solution: Use relative path or check backup directory
```

## Maintenance

### Automated Backups

Create a cron job for automated backups:

```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/project && source venv/bin/activate && python scripts/full_backup.py

# Weekly cleanup of old backups (keep last 10)
0 3 * * 0 cd /path/to/project && find data/backups -name "*.json*" -type f | sort -r | tail -n +11 | xargs rm -f
```

### Monitoring

```bash
# Check backup system health
python scripts/backup_cli.py info

# Validate recent backups
for file in data/backups/comprehensive_backup_*.json.gz; do
    python scripts/backup_cli.py validate "$file"
done
```

### Storage Management

```bash
# Show backup storage usage
python scripts/backup_cli.py info

# Clean old backups (manual)
ls -la data/backups/
rm data/backups/old_backup_file.json.gz
```

## Security Considerations

### Sensitive Data

- **Environment Variables**: API keys and secrets are included in backups
- **Storage**: Store backups in secure, encrypted storage
- **Access Control**: Limit access to backup files
- **Transmission**: Use encrypted channels for backup transfer

### Best Practices

1. **Encrypt Backups**: Encrypt backup files for sensitive data
2. **Secure Storage**: Use secure cloud storage or encrypted drives
3. **Access Logs**: Monitor backup file access
4. **Regular Testing**: Test restore procedures regularly

## Migration from Legacy System

### Compatibility

- **Legacy Format**: v1.0 backups can still be restored
- **New Format**: v2.0 provides comprehensive coverage
- **Mixed Environment**: Both systems can coexist

### Migration Steps

1. Create final legacy backup: `python scripts/generate_backup_json.py`
2. Create new optimized backup: `python scripts/backup_cli.py create --compress`
3. Validate both backups work
4. Switch to optimized system for new backups

## Troubleshooting

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Commands

```bash
# Check system status
python scripts/backup_cli.py info

# Test backup creation
python scripts/backup_cli.py create

# Validate backup
python scripts/backup_cli.py validate backup_file.json.gz

# Dry run restore (validate only)
python scripts/backup_cli.py restore backup_file.json.gz --validate-only
```

### Log Analysis

Logs are written to:
- Console output
- `backup_operations.log` (CLI operations)
- Application logs (programmatic usage)

## API Reference

### Core Classes

#### `OptimizedBackupManager`

Main backup management class.

**Methods:**
- `create_comprehensive_backup(use_compression=True)`: Create backup
- `restore_comprehensive_backup(backup_file, validate_before_restore=True)`: Restore backup
- `_validate_backup_integrity(backup_data)`: Validate backup data

#### Public Functions

- `create_optimized_backup(session, use_compression=True)`: Simple backup creation
- `restore_optimized_backup(session, backup_file, validate=True)`: Simple restore
- `validate_backup_file(backup_file)`: Validate backup file

### Configuration

Environment variables that affect backup behavior:

- `GEMINI_API_KEY`: Included in backup
- `DEBUG`: Affects logging level
- `DB_URL`: Database connection string
- All other environment variables are captured in backup

## Testing

### Unit Tests

```bash
# Run backup system tests
python -m pytest tests/test_optimized_backup.py -v

# Run specific test
python -m pytest tests/test_optimized_backup.py::TestOptimizedBackup::test_comprehensive_backup_creation -v
```

### Integration Tests

```bash
# Full workflow test
python -m pytest tests/test_optimized_backup.py::test_full_backup_restore_workflow -v
```

### Performance Tests

```bash
# Performance benchmarking
python -m pytest tests/test_optimized_backup.py::TestOptimizedBackup::test_bulk_operations_performance -v
```

## Support

For issues with the backup system:

1. Check the logs for error details
2. Validate backup files before restore
3. Use `python scripts/backup_cli.py info` to check system status
4. Run tests to verify system functionality
5. Check file permissions and disk space

## Version History

- **v2.0**: Comprehensive optimized backup system
  - Async operations
  - Bulk SQL operations
  - Comprehensive validation
  - CLI interface
  - Production-ready features
  
- **v1.0**: Legacy backup system
  - Basic JSON export/import
  - Limited validation
  - Synchronous operations
