# AdCP Demo

AdCP Demo with genuine MCP (Model Context Protocol) implementation.

## Quick Start

### Local Development

1. **Setup virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Start the server:**
   ```bash
   make start
   ```

4. **Health check:**
   ```bash
   curl http://localhost:8000/health
   ```

### Development Mode

For development with auto-reload:
```bash
make dev
```

### Testing

Run tests:
```bash
make test
```

Run smoke test:
```bash
make smoke
```

## Make Targets

- `make install` - Install dependencies
- `make start` - Start production server
- `make dev` - Start development server with reload
- `make test` - Run tests
- `make lint` - Lint code (placeholder)
- `make fmt` - Format code (placeholder)
- `make clean` - Clean cache files
- `make smoke` - Run smoke test against localhost:8000

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_URL` | `sqlite:///./data/adcp_demo.sqlite3` | Database connection URL |
| `PORT` | `8000` | Server port |
| `SERVICE_BASE_URL` | `http://localhost:8000` | Service base URL |
| `DEBUG` | `0` | Debug mode |
| `EMBEDDINGS_PROVIDER` | `""` | Embedding provider (e.g., "gemini") |
| `GEMINI_API_KEY` | - | Required if EMBEDDINGS_PROVIDER is set |
| `EMBEDDINGS_MODEL` | `text-embedding-004` | Embedding model name |
| `EMB_CONCURRENCY` | `2` | Embedding worker concurrency (1-8) |
| `EMB_BATCH_SIZE` | `32` | Embedding batch size (1-128) |

### Web Context Grounding

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_WEB_CONTEXT` | `0` | Global flag to enable/disable web grounding |
| `WEB_CONTEXT_TIMEOUT_MS` | `2000` | Timeout for web context fetching (100-10000ms) |
| `WEB_CONTEXT_MAX_SNIPPETS` | `3` | Maximum number of snippets to fetch (1-10) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model to use for web grounding |
| `GEMINI_API_KEY` | - | Required API key for Gemini (only when grounding enabled) |

## Render Deployment

This project is configured for deployment on Render with:

- **Procfile**: Defines web process
- **render.yaml**: Complete deployment configuration
- **Persistent Disk**: `./data` mounted to preserve SQLite database across deploys

### Deployment Steps

1. Connect your repository to Render
2. Render will automatically detect the `render.yaml` configuration
3. The service will be deployed with persistent disk for data storage

### Important Notes

- The `./data` directory is mounted as a persistent disk to preserve SQLite data
- The service binds to `$PORT` for Render compatibility
- Database file: `./data/adcp_demo.sqlite3`
- Embeddings are disabled by default (set `EMBEDDINGS_PROVIDER` to enable)
- Set `GEMINI_API_KEY` in Render environment variables if using embeddings
- Web context grounding is disabled by default (set `ENABLE_WEB_CONTEXT=1` to enable)

## Project Structure

```
/
├── app/                    # Application code
│   ├── main.py            # FastAPI app entry point
│   └── db.py              # Database configuration
├── tests/                  # Test files
├── scripts/                # Utility scripts
├── data/                   # SQLite database (created on startup)
├── reference/              # Reference repositories (read-only)
├── docs/                   # Documentation
│   └── grounding.md        # Web grounding documentation
├── requirements.txt        # Python dependencies
├── Makefile               # Development commands
├── Procfile               # Render/Heroku deployment
├── render.yaml            # Render deployment config
└── README.md              # This file
```

## Health Endpoint

- **URL**: `GET /health`
- **Response**: `{"ok": true, "service": "adcp-demo"}`
- **Purpose**: Monitoring and deployment verification

