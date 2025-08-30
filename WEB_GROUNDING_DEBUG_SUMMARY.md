# Web Grounding Debug Summary

## Issue Identified
The web grounding feature was not working in production because the `ENABLE_WEB_CONTEXT` environment variable was not set in the production environment (render.yaml).

## Root Cause
- Environment variable `ENABLE_WEB_CONTEXT=1` was not configured in production
- Web grounding requires both global flag (`ENABLE_WEB_CONTEXT`) and tenant flag (`enable_web_context`) to be enabled
- Without the global flag, web grounding was disabled regardless of tenant settings

## Changes Made

### 1. Added Debug Logging
**Files Modified:**
- `app/services/_orchestrator_agents.py` - Added comprehensive debug logging to web grounding logic
- `app/utils/env.py` - Added debug logging to environment variable loading
- `app/services/orchestrator.py` - Added debug logging to web_config passing

**Debug Output:**
```
WEB_DEBUG: Starting web grounding check for tenant=test-publisher
WEB_DEBUG: web_config received: {'enabled': True, 'timeout_ms': 3000, ...}
WEB_DEBUG: tenant.enable_web_context attribute exists: True
WEB_DEBUG: tenant.enable_web_context value: True
WEB_DEBUG: Global web grounding is ENABLED
WEB_DEBUG: Tenant web grounding is ENABLED - proceeding with web context fetch
```

### 2. Fixed Production Configuration
**File Modified:**
- `render.yaml` - Added web grounding environment variables

**Added Environment Variables:**
```yaml
- key: ENABLE_WEB_CONTEXT
  value: "1"
- key: WEB_CONTEXT_TIMEOUT_MS
  value: "3000"
- key: WEB_CONTEXT_MAX_SNIPPETS
  value: "3"
- key: GEMINI_MODEL
  value: "gemini-2.5-flash"
```

### 3. Created Comprehensive Tests
**Files Created:**
- `test_web_grounding_debug.py` - Basic configuration and environment tests
- `test_web_grounding_integration.py` - End-to-end integration tests

**Test Coverage:**
- Environment variable parsing (all valid values: 1, true, yes, on, etc.)
- Web grounding configuration loading
- Tenant model web context attribute
- Sales agent with web grounding enabled
- Sales agent with web grounding disabled (global flag off)
- Sales agent with web grounding disabled (tenant flag off)

## Test Results

### Integration Tests ✅
```
✓ All Web Grounding Integration Tests Passed!

Summary:
- Web grounding works when both global and tenant flags are enabled
- Web grounding is disabled when global flag is off (regardless of tenant setting)
- Web grounding is disabled when tenant flag is off (regardless of global setting)
- Environment variables are properly loaded and parsed
- Tenant model correctly supports enable_web_context attribute
- Debug logging is in place for production troubleshooting
```

### Unit Tests ✅
```
4 passed, 6 warnings in 0.67s
```

## Deployment Checklist

### 1. Environment Variables (render.yaml) ✅
- [x] `ENABLE_WEB_CONTEXT=1` - Global web grounding flag
- [x] `WEB_CONTEXT_TIMEOUT_MS=3000` - Timeout for web context requests
- [x] `WEB_CONTEXT_MAX_SNIPPETS=3` - Maximum number of web snippets
- [x] `GEMINI_MODEL=gemini-2.5-flash` - Gemini model for web context

### 2. Code Changes ✅
- [x] Debug logging added to orchestrator agents
- [x] Debug logging added to environment configuration
- [x] Debug logging added to orchestrator
- [x] All tests passing

### 3. Database Schema ✅
- [x] `enable_web_context` column exists in tenant table
- [x] Migration script in place (`app/db.py`)

## Expected Behavior After Deployment

### When Web Grounding is Enabled:
1. **Global Flag**: `ENABLE_WEB_CONTEXT=1` in production
2. **Tenant Flag**: `enable_web_context=True` in database (set via dashboard)
3. **Result**: Web context will be fetched and passed to sales agents

### Debug Logs to Look For:
```
WEB_DEBUG: Loading web grounding configuration from environment variables
WEB_DEBUG: ENABLE_WEB_CONTEXT raw value: '1'
WEB_DEBUG: ENABLE_WEB_CONTEXT parsed as ENABLED
WEB_DEBUG: Final web grounding config: {'enabled': True, ...}
WEB_DEBUG: Orchestrator calling get_web_grounding_config()
WEB_DEBUG: Orchestrator received web_config: {'enabled': True, ...}
WEB_DEBUG: Starting web grounding check for tenant=<tenant-slug>
WEB_DEBUG: Global web grounding is ENABLED
WEB_DEBUG: Tenant web grounding is ENABLED - proceeding with web context fetch
web_grounding tenant=<tenant-slug> enabled=1 model=gemini-2.5-flash snippets=3 ok=true
```

### When Web Grounding is Disabled:
- **Global Flag Off**: `WEB_DEBUG: Global web grounding is DISABLED`
- **Tenant Flag Off**: `WEB_DEBUG: Tenant web grounding is DISABLED - skipping web context fetch`

## Troubleshooting Guide

### If Web Grounding Still Doesn't Work:

1. **Check Environment Variables:**
   ```bash
   # In production logs, look for:
   WEB_DEBUG: ENABLE_WEB_CONTEXT raw value: '1'
   WEB_DEBUG: ENABLE_WEB_CONTEXT parsed as ENABLED
   ```

2. **Check Tenant Settings:**
   ```bash
   # In production logs, look for:
   WEB_DEBUG: tenant.enable_web_context value: True
   WEB_DEBUG: Tenant web grounding is ENABLED
   ```

3. **Check Web Context Fetch:**
   ```bash
   # In production logs, look for:
   WEB_DEBUG: Calling fetch_web_context with timeout=3000, max_snippets=3, model=gemini-2.5-flash
   WEB_DEBUG: Web context fetch successful, got 3 snippets
   ```

4. **Common Issues:**
   - Environment variable not set: Look for `WEB_DEBUG: ENABLE_WEB_CONTEXT raw value: 'NOT_SET'`
   - Tenant flag not set: Look for `WEB_DEBUG: tenant.enable_web_context value: False`
   - Web context fetch failure: Look for `WEB_DEBUG: Web context fetch failed with exception:`

## Next Steps

1. **Deploy to Production:**
   - Commit and push changes to trigger Render deployment
   - Monitor deployment logs for any errors

2. **Verify in Production:**
   - Check production logs for debug messages
   - Test web grounding with a tenant that has it enabled
   - Verify web context is being fetched and passed to sales agents

3. **Monitor Performance:**
   - Watch for any performance impact from web context fetching
   - Monitor Gemini API usage and costs
   - Check for any timeout or error issues

## Files Modified Summary

```
Modified:
- app/services/_orchestrator_agents.py (added debug logging)
- app/utils/env.py (added debug logging)
- app/services/orchestrator.py (added debug logging)
- render.yaml (added environment variables)

Created:
- test_web_grounding_debug.py (debug tests)
- test_web_grounding_integration.py (integration tests)
- WEB_GROUNDING_DEBUG_SUMMARY.md (this file)
```

The web grounding feature should now work correctly in production once deployed with the updated environment variables.
