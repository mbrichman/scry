# Scry

[![Docker](https://img.shields.io/badge/docker-ghcr.io-blue?logo=docker)](https://ghcr.io/mbrichman/Scry)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Own your AI conversations.** Scry is a self-hosted conversation archive that keeps your AI chat history private, searchable, and portable across providers.

## Why Scry?

### Privacy First
Your conversations contain personal thoughts, business ideas, and sensitive information that have no business being hosted by "big tech" on the public internet. Scry keeps everything local on your own machine—no cloud services, no telemetry, no data leaving your infrastructure. Your PostgreSQL database, your data, your control.

### Provider Portability
Don't let your conversation history be locked into one AI provider. Scry imports from ChatGPT, Claude, and OpenWebUI, giving you a unified archive that survives provider switches, account changes, or service shutdowns. 

### OpenWebUI Integration
Seamlessly sync conversations with [Open WebUI](https://openwebui.com/)—pull your history into Scry for archival, or export conversations back to OpenWebUI. Use OpenWebUI as your AI frontend while Scry serves as your permanent, searchable archive.

## Features

- **Multi-Source Import**: ChatGPT JSON exports, Claude conversations, OpenWebUI API sync
- **Smart Search**: Combined full-text and semantic vector search for finding exactly what you need
- **RAG Integration**: Contextual retrieval for AI-powered search with surrounding conversation context
- **Background Sync**: Automatic OpenWebUI synchronization with change detection
- **Self-Contained**: Runs entirely on your own hardware with Docker

## Quick Start

```bash
# Pull the image
docker pull ghcr.io/mbrichman/Scry:main

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Start the stack
docker compose up -d

# Access the application
open http://localhost:5001
```

## Environment Variables

Create a `.env` file (use `.env.example` as a template):

```env
# PostgreSQL credentials
POSTGRES_USER=Scry
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=Scry

# Application settings
SECRET_KEY=your-secret-key-here
```

## OpenWebUI Sync

To sync conversations from OpenWebUI:

1. Go to **Settings** in Scry
2. Enter your OpenWebUI URL (e.g., `https://your-openwebui-instance`)
3. Add your OpenWebUI API key
4. Click **Sync** to pull conversations

Scry tracks sync state and only fetches new or updated conversations on subsequent syncs.

## Architecture

```
Scry/
├── api/                  # REST API endpoints
├── controllers/          # Request handlers
├── db/
│   ├── models/          # SQLAlchemy models
│   ├── repositories/    # Data access layer
│   ├── services/        # Business logic
│   │   ├── search_service.py          # Hybrid FTS + vector search
│   │   ├── import_service.py          # Multi-format import
│   │   ├── sync_service.py            # OpenWebUI sync
│   │   └── contextual_retrieval_service.py  # RAG context windows
│   └── workers/         # Background embedding generation
├── templates/           # Web UI (Jinja2)
└── tests/               # Test suite
```

## Tech Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: PostgreSQL 17 with pgvector
- **Search**: PostgreSQL FTS + sentence-transformers embeddings
- **Deployment**: Docker & Docker Compose

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/conversations` | List conversations |
| `GET /api/search?q=...` | Search conversations |
| `POST /api/rag/query` | Contextual RAG retrieval |
| `POST /api/sync/openwebui` | Trigger OpenWebUI sync |
| `GET /api/sync/status` | Check sync progress |

## Development

```bash
# Run tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# With coverage
pytest --cov=. --cov-report=html
```

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Ensure tests pass: `pytest`
4. Push and create a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.
