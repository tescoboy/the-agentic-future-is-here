# MCP (Model Context Protocol) Implementation

## Overview

The AdCP Demo implements MCP JSON-RPC for agent communication, providing both client and server capabilities.

## MCP Client

### Features

- **Session Management**: Automatic session lifecycle with UUID4 session IDs
- **Auto-retry**: Single retry on session-required errors (HTTP 401/412)
- **Timeout Handling**: Configurable timeouts with clear error messages
- **Circuit Breaker**: Per-agent failure tracking and suppression

### Usage

```python
from app.services.mcp_client import MCPClient

# Initialize client
client = MCPClient(base_url="http://agent.example.com/mcp", timeout=8000)

# Open session
await client.open()

# Make RPC call
result = await client.call("get_products", {"brief": "marketing campaign"})

# Close session
await client.close()
```

### Configuration

Environment variables:
- `ORCH_TIMEOUT_MS_DEFAULT`: Default timeout in milliseconds (default: 8000)
- `MCP_SESSION_TTL_S`: Session TTL in seconds (default: 60)

## MCP Server

### Endpoints

- `POST /mcp/agents/{tenant_slug}/rpc`: JSON-RPC endpoint
- `POST /mcp/agents/{tenant_slug}/rank`: REST shim for Sales agents
- `DELETE /mcp/agents/{tenant_slug}/rpc`: Session cleanup

### Supported Methods

- `mcp.get_info`: Returns service capabilities
- `rank_products`: Ranks products for a given brief (Sales agents only)

### Session Management

- Sessions are tenant-specific
- TTL-based expiration (configurable via `MCP_SESSION_TTL_S`)
- Lazy cleanup on validation

### Error Codes

- `-32600`: Invalid request (malformed envelope)
- `-32601`: Method not found
- `-32602`: Invalid params (missing brief, unknown tenant)
- `-32000`: Server error (session invalid, internal errors)

## Logging

All MCP operations are logged at INFO level:

```
opened mcp client base=agent.example.com session=short
rpc id=1 method=rank_products outcome=result
closed mcp client session=short
```

No payloads or sensitive data are logged.

## Testing

Use the smoke script to test MCP connectivity:

```bash
./scripts/smoke.sh
```

## Troubleshooting

### Common Issues

1. **Session Required Errors**: Ensure client calls `open()` before `call()`
2. **Timeout Errors**: Check network connectivity and increase timeout if needed
3. **Method Not Found**: Verify the agent supports the requested method
4. **Invalid Params**: Check parameter structure matches agent expectations

### Debug Mode

Set `DEBUG=1` to enable additional logging and probe endpoints.

