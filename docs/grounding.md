# Web Context Grounding

## Overview

Web Context Grounding is a feature that enriches AI-powered product ranking with fresh, real-time information from Google Search. When enabled, the system fetches relevant market insights, audience trends, and recent programming information to provide more accurate and up-to-date product recommendations.

## How It Works

1. **RAG Pre-filter**: The existing RAG (Retrieval-Augmented Generation) system pre-filters products based on semantic similarity to the buyer brief.

2. **Web Context Fetching**: If enabled, the system uses Google's Gemini API with the `google_search` tool to fetch fresh web context relevant to the campaign brief.

3. **AI Ranking**: The AI ranking system receives both the pre-filtered products and web context snippets, enabling more informed product recommendations.

4. **Result Aggregation**: Final results are returned with enhanced reasoning based on current market conditions.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_WEB_CONTEXT` | `0` | Global flag to enable/disable web grounding |
| `WEB_CONTEXT_TIMEOUT_MS` | `2000` | Timeout for web context fetching (100-10000ms) |
| `WEB_CONTEXT_MAX_SNIPPETS` | `3` | Maximum number of snippets to fetch (1-10) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model to use for web grounding |
| `GEMINI_API_KEY` | - | Required API key for Gemini (only when grounding enabled) |

### Tenant-Level Toggle

Each tenant can independently enable or disable web context grounding through their publisher dashboard, regardless of the global setting.

## Enabling Web Grounding

### Global Configuration

1. Set environment variables:
   ```bash
   ENABLE_WEB_CONTEXT=1
   GEMINI_API_KEY=your_api_key_here
   ```

2. Optionally customize:
   ```bash
   WEB_CONTEXT_TIMEOUT_MS=3000
   WEB_CONTEXT_MAX_SNIPPETS=5
   GEMINI_MODEL=gemini-2.5-flash
   ```

### Per-Tenant Configuration

1. Navigate to the publisher dashboard for your tenant
2. Find the "AI Enrichment Settings" card
3. Toggle "Enable Web Context Grounding"
4. Click "Save Settings"

## Supported Models

| Model | Tool | Notes |
|-------|------|-------|
| Gemini 2.5 Pro | `google_search` | Recommended for production |
| Gemini 2.5 Flash | `google_search` | Fast and cost-effective |
| Gemini 2.5 Flash-Lite | `google_search` | Lightweight option |
| Gemini 2.0 Flash | `google_search` | Legacy 2.0 models |
| Gemini 1.5 Pro | `google_search_retrieval` | Legacy with dynamic mode |
| Gemini 1.5 Flash | `google_search_retrieval` | Legacy with dynamic mode |

## Costs and Performance

### Costs
- **API Calls**: Each web grounding request counts as one Gemini API call
- **Search Queries**: Multiple search queries within a single request count as one billable use
- **Pricing**: Follows standard Gemini API pricing

### Performance Impact
- **Latency**: Adds 1-3 seconds to response time (configurable via timeout)
- **Throughput**: Limited by Gemini API rate limits
- **Fallback**: System continues without web context if grounding fails

## Error Handling

### Graceful Degradation
The system is designed to continue functioning even when web grounding fails:

- **Missing API Key**: System proceeds without web context
- **Quota Exceeded**: System proceeds without web context
- **Timeout**: System proceeds without web context
- **Network Issues**: System proceeds without web context

### Error Tracking
When web grounding fails, the system:
1. Logs the failure with tenant and model information
2. Sets `web_context_unavailable=true` in per-agent errors
3. Continues with RAG pre-filter results only

## Privacy and Security

### Data Handling
- **Brief Content**: Never logged in web grounding operations
- **Snippet Content**: Never logged in web grounding operations
- **Search Queries**: Never logged in web grounding operations
- **Metadata**: Captured for future citation features but not logged

### API Key Security
- Store `GEMINI_API_KEY` securely in environment variables
- Never expose API keys in logs or error messages
- Use different API keys for different environments

## Monitoring and Logging

### Log Format
```
web_grounding tenant=<slug> enabled=<0|1> model=<model> snippets=<N> ok=<true|false>
```

### Debug Information
Optional debug logging includes:
- Code path (2.5 vs 1.5)
- Tool name used
- Timing in milliseconds

## Troubleshooting

### Common Issues

1. **"web grounding enabled but GEMINI_API_KEY missing"**
   - Solution: Set the `GEMINI_API_KEY` environment variable

2. **"web grounding quota or authorization error"**
   - Solution: Check API key validity and quota limits

3. **"web grounding timeout after Xms"**
   - Solution: Increase `WEB_CONTEXT_TIMEOUT_MS` or check network connectivity

4. **"web grounding unsupported for model X"**
   - Solution: Use a supported model from the table above

### Debugging Steps

1. Check environment variables are set correctly
2. Verify API key has sufficient quota
3. Test with a supported model
4. Check network connectivity to Gemini API
5. Review application logs for detailed error messages

## Future Enhancements

### Planned Features
- **Inline Citations**: Display source links for web context
- **Caching**: Cache web context results to reduce API calls
- **Advanced Filtering**: More sophisticated snippet filtering
- **Custom Prompts**: Tenant-specific web context prompts

### API Improvements
- **Batch Processing**: Process multiple briefs in a single API call
- **Streaming**: Real-time web context updates
- **Custom Sources**: Integration with additional data sources

## Migration Notes

### Database Changes
The feature adds an `enable_web_context` column to the `tenants` table:
```sql
ALTER TABLE tenants ADD COLUMN enable_web_context INTEGER DEFAULT 0;
```

### Backward Compatibility
- Feature is disabled by default
- No breaking changes to existing APIs
- Existing tenants continue to work without modification
- RAG pre-filter remains the primary ranking mechanism

## Support

For issues related to web grounding:
1. Check the troubleshooting section above
2. Review application logs for error details
3. Verify environment configuration
4. Test with a simple brief to isolate issues
