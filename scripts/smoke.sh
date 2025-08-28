#!/bin/sh
# Smoke test script for AdCP Demo
# Tests basic server functionality and agent connectivity

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
TIMEOUT=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[SMOKE]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test health endpoint
log "Testing health endpoint..."
if ! curl -s --max-time $TIMEOUT "$BASE_URL/health" > /dev/null; then
    error "Health check failed"
    exit 1
fi

# Test preflight endpoint
log "Testing preflight endpoint..."
PREFLIGHT_RESPONSE=$(curl -s --max-time $TIMEOUT "$BASE_URL/preflight")
if [ $? -ne 0 ]; then
    error "Preflight check failed"
    exit 1
fi

# Extract tenant count from preflight response (simplified)
TENANT_COUNT=$(echo "$PREFLIGHT_RESPONSE" | grep -o '"count":[[:space:]]*[0-9]*' | cut -d: -f2 | tr -d ' ' || echo "0")

if [ "$TENANT_COUNT" -gt 0 ] 2>/dev/null; then
    log "Found $TENANT_COUNT tenants, testing Sales REST shim..."
    
    # Get first tenant slug (simplified - in real usage you'd parse JSON properly)
    TENANT_SLUG=$(echo "$PREFLIGHT_RESPONSE" | grep -o '"slug":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")
    
    if [ -n "$TENANT_SLUG" ]; then
        # Test Sales REST shim
        SALES_RESPONSE=$(curl -s --max-time $TIMEOUT \
            -X POST \
            -H "Content-Type: application/json" \
            -d '{"brief":"smoke test brief"}' \
            "$BASE_URL/mcp/agents/$TENANT_SLUG/rank")
        
        if [ $? -eq 0 ]; then
            log "Sales REST shim test passed"
        else
            warn "Sales REST shim test failed"
        fi
    else
        warn "No tenant slug found for Sales test"
    fi
else
    warn "No tenants found, skipping Sales REST test"
fi

# Check for MCP signals agents
MCP_SIGNALS_COUNT=$(echo "$PREFLIGHT_RESPONSE" | grep -o '"mcp":[[:space:]]*[0-9]*' | head -1 | cut -d: -f2 | tr -d ' ' || echo "0")

if [ "$MCP_SIGNALS_COUNT" -gt 0 ] 2>/dev/null; then
    log "Found $MCP_SIGNALS_COUNT MCP signals agents"
    # Note: Actual MCP testing would require external agent setup
    # This is just informational for now
else
    log "No MCP signals agents found"
fi

log "Smoke test completed successfully"
