# Agents Configuration Guide

## Overview

The AdCP Demo supports two types of agents:
- **Sales Agents**: Rank products based on buyer briefs
- **Signals Agents**: Provide market signals and insights

## Agent Types

### Sales Agents

Sales agents rank products for buyer briefs using the `rank_products` method.

**Internal Sales Agents (Tenants)**:
- Protocol: MCP (default)
- Endpoint: `/mcp/agents/{tenant_slug}/rpc`
- REST Shim: `/mcp/agents/{tenant_slug}/rank`

**External Sales Agents**:
- Protocol: MCP or REST
- Configuration via ExternalAgents table

### Signals Agents

Signals agents provide market insights using the `get_signals` method.

**External Signals Agents**:
- Protocol: MCP only
- Configuration via ExternalAgents table

## Configuration

### Internal Sales Agents (Tenants)

1. Create a tenant via the admin UI or API
2. Add products to the tenant
3. Optionally set a custom prompt for the tenant

```sql
INSERT INTO tenants (slug, name, enabled) VALUES ('acme', 'Acme Corp', 1);
```

### External Agents

Configure external agents via the admin UI or API:

```sql
INSERT INTO external_agents (
    name, base_url, agent_type, protocol, enabled
) VALUES (
    'Market Signals Pro',
    'https://signals.example.com/mcp',
    'signals',
    'mcp',
    1
);
```

## Agent Protocols

### MCP Protocol

- **Method**: `rank_products` (Sales) or `get_signals` (Signals)
- **Params**: `{"brief": "buyer brief text"}`
- **Response**: Structured JSON with items and scores

### REST Protocol (Sales only)

- **Endpoint**: `POST {base_url}/rank`
- **Body**: `{"brief": "buyer brief text"}`
- **Response**: Same structure as MCP

## Testing Agents

### Probe Endpoints

When `DEBUG=1`, probe endpoints are available:

- `POST /external-agents/{id}/probe`: Test agent connectivity
- `GET /external-agents/{id}/probe`: View probe results

### Smoke Testing

Use the smoke script to test agent connectivity:

```bash
# Test with default localhost
./scripts/smoke.sh

# Test with custom URL
BASE_URL=https://your-server.com ./scripts/smoke.sh
```

## Troubleshooting

### Common Issues

1. **Agent Not Responding**:
   - Check `base_url` is correct and accessible
   - Verify agent is running and healthy
   - Check network connectivity

2. **Protocol Errors**:
   - Ensure protocol matches agent implementation
   - Signals agents must use MCP protocol
   - Check agent supports required methods

3. **Authentication Issues**:
   - Verify agent doesn't require authentication
   - Check for CORS issues with external agents

4. **Timeout Errors**:
   - Increase `ORCH_TIMEOUT_MS_DEFAULT` if needed
   - Check agent response times

### Debug Mode

Enable debug mode for detailed logging:

```bash
export DEBUG=1
make dev
```

This enables:
- Probe endpoints for external agents
- Additional logging
- Detailed error messages

## Best Practices

1. **Start Small**: Begin with internal sales agents before adding external agents
2. **Test Thoroughly**: Use probe endpoints to verify agent connectivity
3. **Monitor Performance**: Watch for timeout and circuit breaker events
4. **Secure URLs**: Use HTTPS for external agents in production
5. **Regular Testing**: Run smoke tests regularly to catch issues early

