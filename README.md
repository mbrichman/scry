# Dovos

[![Docker](https://img.shields.io/badge/docker-ghcr.io-blue?logo=docker)](https://ghcr.io/mbrichman/dovos)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A chat conversation archive and search application with PostgreSQL full-text search, RAG (Retrieval-Augmented Generation) integration, and OpenWebUI compatibility.

## Description

Dovos is a Flask-based web application designed to import, archive, and search through chat conversations from multiple sources (ChatGPT, Claude, etc.). It features:

- **Full-Text Search**: PostgreSQL-backed FTS for fast, accurate conversation search
- **Vector Search**: Semantic search with pgvector embeddings
- **Hybrid Search**: Combined FTS and vector similarity ranking
- **OpenWebUI Compatibility**: Export and integration with Open WebUI
- **PostgreSQL Backend**: Enterprise-grade database with proper ACID guarantees
- **Chat Import**: Support for ChatGPT and Claude conversation formats
- **Modern Web UI**: Flask-based interface with Jinja2 templates

## Setup and Installation

### Requirements

- Docker and Docker Compose
- No additional dependencies needed

### Quick Start

**Pull from GitHub Container Registry:**

```bash
# Pull the latest image
docker pull ghcr.io/mbrichman/dovos:main

# Or pull a specific version
docker pull ghcr.io/mbrichman/dovos:v1.0.0
```

**Run with Docker Compose:**

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 2. Start the entire stack (migrations run automatically)
docker compose up -d

# 3. Access the application
open http://localhost:5001
```

### Environment Variables

Create a `.env` file in the project root (use `.env.example` as a template):

```env
# PostgreSQL credentials
POSTGRES_USER=dovos
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=dovos

# Application settings
SECRET_KEY=your-secret-key-here
```

## Directory Structure

```
dovos/
├── alembic/              # Database migrations
├── api/                  # API endpoints
├── controllers/          # MVC controllers
├── data/                 # Application data (ignored by git)
│   └── source/          # Source conversation files
├── db/                   # Database layer
│   ├── adapters/        # Legacy API format adapter
│   ├── models/          # SQLAlchemy models
│   ├── repositories/    # Repository pattern implementations
│   ├── services/        # Business logic services
│   └── workers/         # Background workers (embedding, etc.)
├── docs/                 # Project documentation
├── models/              # Legacy models (being migrated)
├── scripts/             # Utility scripts
│   ├── archived/       # Deprecated scripts (gitignored)
│   ├── database/       # DB maintenance scripts
│   └── utils/          # General utility scripts
├── static/              # Static web assets
├── templates/           # Jinja2 templates
├── tests/               # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   ├── e2e/            # End-to-end tests
│   └── fixtures/       # Test fixtures
├── app.py               # Flask application entry point
├── config/              # Application configuration
├── routes.py            # Web routes
└── requirements.txt     # Python dependencies
```

## Development Workflow

### Code Style

- Python: Follow PEP 8 guidelines
- Use type hints where applicable
- Run `python -m compileall -q .` to check for syntax errors

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Ensure tests pass: `pytest`
4. Commit with descriptive messages
5. Push and create a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
