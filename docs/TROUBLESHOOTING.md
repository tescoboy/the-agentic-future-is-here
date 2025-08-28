# Troubleshooting Guide

## Quick Diagnostics

### Preflight Check

Always start with the preflight dashboard:

```bash
# JSON endpoint
curl http://localhost:8000/preflight

# Web dashboard
open http://localhost:8000/preflight/ui
```

This shows system status, environment variables, and component health.

### Smoke Test

Run the smoke test to verify basic functionality:

```bash
./scripts/smoke.sh
```

## Common Issues

### Startup Problems

#### 1. Reference Repos Missing

**Error**: `Missing reference repos. Clone them exactly as follows:`

**Solution**:
```bash
git clone https://github.com/adcontextprotocol/salesagent reference/salesagent
git clone https://github.com/adcontextprotocol/signals-agent reference/signals-agent
```

#### 2. Database Issues

**Error**: `Database writeable: false`

**Solutions**:
- Check file permissions: `ls -la ./data/`
- Ensure disk space: `df -h`
- Verify SQLite is working: `sqlite3 ./data/adcp_demo.sqlite3 "SELECT 1;"`

#### 3. Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Runtime Issues

#### 1. Agent Connection Failures

**Symptoms**: Timeout errors, circuit breaker trips

**Diagnostics**:
```bash
# Test agent directly
curl -X POST https://agent.example.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"mcp.get_info","params":{}}'

# Check preflight for agent status
curl http://localhost:8000/preflight | jq '.agents'
```

**Solutions**:
- Verify agent URL is correct and accessible
- Check agent is running and healthy
- Increase timeout: `export ORCH_TIMEOUT_MS_DEFAULT=15000`

#### 2. MCP Session Errors

**Error**: `session required` or `session invalid`

**Solution**: This is usually handled automatically by the client. If persistent:
- Check MCP_SESSION_TTL_S setting
- Verify agent supports sessions
- Restart the application

#### 3. Database Schema Issues

**Error**: `external_agents_has_agent_type: false`

**Solution**: Run migrations:
```bash
# Check current schema
sqlite3 ./data/adcp_demo.sqlite3 ".schema external_agents"

# Restart app to run migrations
make restart
```

### Buyer UI Issues

#### 1. No Agents Available

**Symptoms**: Empty agent list in buyer form

**Check**:
- Verify tenants exist and are enabled
- Check external agents are enabled
- Look at preflight dashboard agent counts

#### 2. Brief Submission Fails

**Symptoms**: Form submission errors

**Diagnostics**:
- Check browser console for errors
- Verify at least one agent is selected
- Ensure brief is not empty

#### 3. No Results Displayed

**Symptoms**: Empty results page

**Check**:
- Verify agents have products (for sales agents)
- Check score threshold (≥70% items only)
- Look for agent errors in results

### Performance Issues

#### 1. Slow Response Times

**Diagnostics**:
```bash
# Check orchestrator timeouts
curl http://localhost:8000/preflight | jq '.env.ORCH_TIMEOUT_MS_DEFAULT'

# Monitor logs for timeout errors
tail -f logs/app.log | grep timeout
```

**Solutions**:
- Increase `ORCH_TIMEOUT_MS_DEFAULT`
- Reduce `ORCH_CONCURRENCY` if agents are slow
- Check agent performance

#### 2. Circuit Breaker Trips

**Symptoms**: Agents consistently fail

**Check**:
- Agent health and connectivity
- Network issues
- Agent configuration

**Solutions**:
- Fix underlying agent issues
- Adjust `CB_FAILS` and `CB_TTL_S` settings
- Restart application to reset circuit breakers

## Debug Mode

Enable debug mode for detailed diagnostics:

```bash
export DEBUG=1
make dev
```

This enables:
- Probe endpoints for external agents
- Additional logging
- Detailed error messages

## Log Analysis

### Key Log Patterns

**Successful MCP calls**:
```
opened mcp client base=agent.example.com session=short
rpc id=1 method=rank_products outcome=result
closed mcp client session=short
```

**Timeout errors**:
```
timeout after 8000ms
```

**Circuit breaker trips**:
```
circuit breaker tripped for agent.example.com
```

### Log Locations

- Application logs: Console output (development)
- Error logs: Check stderr for exceptions
- Access logs: Not implemented (use web server logs if behind proxy)

## Environment Variables

### Required Variables

- `DB_URL`: Database connection string
- `SERVICE_BASE_URL`: Base URL for internal service calls

### Optional Variables

- `ORCH_TIMEOUT_MS_DEFAULT`: Orchestrator timeout (default: 8000)
- `ORCH_CONCURRENCY`: Max concurrent agent calls (default: 8)
- `CB_FAILS`: Circuit breaker failure threshold (default: 2)
- `CB_TTL_S`: Circuit breaker cooldown (default: 60)
- `MCP_SESSION_TTL_S`: MCP session TTL (default: 60)
- `DEBUG`: Enable debug mode (0 or 1)

## Getting Help

1. **Check preflight dashboard first**
2. **Run smoke test**
3. **Enable debug mode**
4. **Check logs for specific errors**
5. **Verify environment variables**
6. **Test individual components**

For persistent issues, collect:
- Preflight JSON output
- Smoke test results
- Relevant log excerpts
- Environment variable values

