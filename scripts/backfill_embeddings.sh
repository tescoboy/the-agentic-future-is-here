#!/bin/bash

# Embeddings backfill script
# Usage: ./scripts/backfill_embeddings.sh [--limit 1000] [--batch 64]

set -e

# Default values
LIMIT=1000
BATCH_SIZE=64

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --batch)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [--limit 1000] [--batch 64]"
            echo ""
            echo "Options:"
            echo "  --limit N    Maximum number of products to process (default: 1000)"
            echo "  --batch N    Batch size for processing (default: 64)"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate arguments
if ! [[ "$LIMIT" =~ ^[0-9]+$ ]] || [ "$LIMIT" -lt 1 ]; then
    echo "Error: --limit must be a positive integer"
    exit 1
fi

if ! [[ "$BATCH_SIZE" =~ ^[0-9]+$ ]] || [ "$BATCH_SIZE" -lt 1 ] || [ "$BATCH_SIZE" -gt 128 ]; then
    echo "Error: --batch must be between 1 and 128"
    exit 1
fi

echo "🚀 Starting embeddings backfill..."
echo "   Limit: $LIMIT products"
echo "   Batch size: $BATCH_SIZE"
echo ""

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "Error: Must run from project root directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Virtual environment not detected"
    echo "Make sure to activate your virtual environment first"
    echo ""
fi

# Create a temporary Python script for backfill
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOF'
#!/usr/bin/env python3

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import get_session
from app.services.embeddings_backfill import backfill_once, find_products_needing_embeddings
from app.utils.embeddings_config import validate_embeddings_setup

async def main():
    limit = int(sys.argv[1])
    batch_size = int(sys.argv[2])
    
    try:
        # Validate embeddings configuration
        validate_embeddings_setup()
        print("✅ Embeddings configuration validated")
    except Exception as e:
        print(f"❌ Embeddings configuration error: {e}")
        sys.exit(1)
    
    session = next(get_session())
    total_processed = 0
    total_successful = 0
    total_failed = 0
    
    try:
        while total_processed < limit:
            # Check how many products need embeddings
            remaining = len(find_products_needing_embeddings(session, limit=1))
            if remaining == 0:
                print("✅ No more products need embeddings")
                break
            
            # Process one batch
            result = await backfill_once(session, batch_size)
            
            if result['processed'] == 0:
                print("✅ No more products to process")
                break
            
            total_processed += result['processed']
            total_successful += result['successful']
            total_failed += result['failed']
            
            print(f"📦 Batch completed: {result['processed']} processed, "
                  f"{result['successful']} successful, {result['failed']} failed")
            
            if result['remaining'] == 0:
                print("✅ All products processed")
                break
            
            if total_processed >= limit:
                print(f"⏹️  Reached limit of {limit} products")
                break
        
        print("")
        print("📊 Final Results:")
        print(f"   Total processed: {total_processed}")
        print(f"   Successful: {total_successful}")
        print(f"   Failed: {total_failed}")
        
        if total_failed > 0:
            print("⚠️  Some products failed to embed. Check logs for details.")
            sys.exit(1)
        else:
            print("✅ Backfill completed successfully")
            
    except Exception as e:
        print(f"❌ Backfill failed: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Run the backfill script
python3 "$TEMP_SCRIPT" "$LIMIT" "$BATCH_SIZE"

# Clean up
rm "$TEMP_SCRIPT"

echo ""
echo "🎉 Backfill script completed"
