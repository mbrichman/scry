# Test Infrastructure Setup - Phase 1.0 ✅ COMPLETE

**Status**: Phase 1.0 Complete  
**Date**: 2025-10-22

## Summary

The test infrastructure for PostgreSQL migration validation is now complete. You can begin writing migration validation tests immediately.

## What Was Built

### 1. Test Database (Docker Compose)
- **File**: `docker-compose.test.yml`
- **Database**: PostgreSQL 16 with pgvector extension
- **Port**: 5433 (separate from dev database on 5432)
- **Extensions**: vector, pg_trgm, uuid-ossp

### 2. Test Configuration
- **File**: `pytest.ini`
- **New Markers**: `migration`, `unit`, `integration`, `contract`, `perf`
- **Coverage**: Configured for coverage reports

### 3. Test Utilities

#### Fake Embeddings (`tests/utils/fake_embeddings.py`)
- Fast, deterministic 384-dim vectors
- No ML model loading required
- Hash-based seeding for reproducibility
- Usage:
  ```python
  from tests.utils.fake_embeddings import generate_fake_embedding
  embedding = generate_fake_embedding("test text")
  ```

#### Data Seeding (`tests/utils/seed.py`)
- Factory functions for all models
- Realistic test data
- Usage:
  ```python
  from tests.utils.seed import seed_conversation_with_messages
  
  with get_unit_of_work() as uow:
      conv, messages = seed_conversation_with_messages(
          uow,
          title="Test Conversation",
          message_count=4,
          with_embeddings=True
      )
  ```

### 4. Pytest Fixtures (`tests/conftest.py`)

Key fixtures available:
- `test_db_engine` - Test database engine (session scope)
- `db_session` - Clean database session per test (auto-rollback)
- `uow` - Unit of Work with test session
- `seed_conversations` - Factory for seeding test data
- `toggle_postgres_mode` - Switch between PostgreSQL and legacy backends
- `both_backends` - Test both backends with identical data

### 5. Test Fixtures (`tests/fixtures/`)

Real conversation samples extracted:
- **ChatGPT**: 6-message conversation
- **Claude**: 4-message conversation
- **Location**: `tests/fixtures/{chatgpt,claude}/sample_conversation.json`

### 6. Directory Structure

```
tests/
├── conftest.py              # Pytest configuration with fixtures
├── fixtures/
│   ├── chatgpt/            # ChatGPT export samples
│   ├── claude/             # Claude export samples
│   ├── large/              # Large datasets (to be added)
│   ├── golden_responses/   # API baselines (populated by tests)
│   ├── extract_samples.py  # Sample extraction script
│   └── README.md
├── utils/
│   ├── fake_embeddings.py  # Deterministic embeddings
│   └── seed.py             # Data factories
├── unit/                   # Unit tests
├── integration/            # Integration tests
├── migration/              # Migration validation tests (NEW)
├── contract/               # Contract tests (NEW)
├── ui/                     # UI tests (NEW)
└── perf/                   # Performance tests (NEW)
```

## Quick Start

### 1. Start Test Database

```bash
# Start the test database
docker compose -f docker-compose.test.yml up -d

# Verify it's running
docker compose -f docker-compose.test.yml ps

# Check logs if needed
docker compose -f docker-compose.test.yml logs postgres-test
```

### 2. Run Sample Test

Create a simple test to verify setup:

```python
# tests/test_infrastructure.py
import pytest
from tests.utils.seed import seed_conversation_with_messages
from tests.utils.fake_embeddings import generate_fake_embedding

@pytest.mark.unit
def test_database_connection(db_session):
    """Verify database connection works."""
    result = db_session.execute("SELECT 1")
    assert result.scalar() == 1

@pytest.mark.unit
def test_seed_conversation(uow):
    """Verify seeding works."""
    conv, messages = seed_conversation_with_messages(
        uow,
        message_count=3,
        with_embeddings=False
    )
    assert conv.id is not None
    assert len(messages) == 3

@pytest.mark.unit
def test_fake_embeddings():
    """Verify fake embeddings work."""
    embedding = generate_fake_embedding("test")
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)
```

Run it:
```bash
pytest tests/test_infrastructure.py -v
```

### 3. Run Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only migration tests
pytest -m migration

# Skip slow tests
pytest -m "not slow"

# Run with coverage
pytest -m unit --cov=db --cov-report=html
```

### 4. Use Fixtures in Tests

```python
@pytest.mark.unit
def test_with_seeded_data(seed_conversations):
    """Test using seed_conversations fixture."""
    # Seed 5 conversations with 4 messages each
    conversations = seed_conversations(
        count=5,
        messages_per_conversation=4,
        with_embeddings=True
    )
    assert len(conversations) == 5

@pytest.mark.migration
def test_both_backends(both_backends):
    """Test API parity between backends."""
    # Test with PostgreSQL
    pg_result = both_backends.with_postgres(
        lambda: call_api_endpoint()
    )
    
    # Test with legacy
    legacy_result = both_backends.with_legacy(
        lambda: call_api_endpoint()
    )
    
    assert pg_result == legacy_result
```

## Environment Variables

The test infrastructure uses these environment variables:

```bash
# Test database URL (default shown)
export TEST_DATABASE_URL="postgresql+psycopg://test_user:test_password@localhost:5433/dovos_test"

# Toggle PostgreSQL mode
export USE_POSTGRES="true"  # or "false" for legacy mode
```

## Database Management

```bash
# Start test database
docker compose -f docker-compose.test.yml up -d

# Stop test database (keeps data)
docker compose -f docker-compose.test.yml stop

# Stop and remove (clean slate)
docker compose -f docker-compose.test.yml down

# Remove with volumes (complete clean)
docker compose -f docker-compose.test.yml down -v

# View logs
docker compose -f docker-compose.test.yml logs -f postgres-test

# Connect to test database
psql postgresql://test_user:test_password@localhost:5433/dovos_test
```

## Next Steps

You're now ready to proceed with **Phase 1.1: API Contract Compliance Tests**.

Key tasks for Phase 1.1:
1. Create `tests/migration/test_api_contract_compliance.py`
2. Test all 15+ API endpoints for parity
3. Capture golden responses
4. Validate JSON schemas match exactly

See `docs/TEST_PLAN_POSTGRES_MIGRATION.md` for full details.

## Troubleshooting

### Database Connection Fails

```bash
# Check if container is running
docker ps | grep dovos-test

# Check container logs
docker compose -f docker-compose.test.yml logs postgres-test

# Restart container
docker compose -f docker-compose.test.yml restart
```

### Import Errors

```bash
# Make sure you're in the project root
cd /Users/markrichman/projects/dovos

# Verify Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Install test dependencies if needed
pip install pytest pytest-cov sqlalchemy psycopg numpy
```

### Permission Issues

```bash
# Fix fixture directory permissions
chmod -R 755 tests/fixtures

# Make extract script executable
chmod +x tests/fixtures/extract_samples.py
```

## Files Created

**Configuration:**
- `docker-compose.test.yml`
- `scripts/database/init-test-db.sql`
- `pytest.ini` (updated)

**Utilities:**
- `tests/utils/fake_embeddings.py`
- `tests/utils/seed.py`
- `tests/conftest.py` (updated)

**Fixtures:**
- `tests/fixtures/chatgpt/sample_conversation.json`
- `tests/fixtures/claude/sample_conversation.json`
- `tests/fixtures/extract_samples.py`
- `tests/fixtures/README.md`

**Documentation:**
- `docs/TEST_INFRASTRUCTURE_SETUP.md` (this file)
- `docs/TEST_PLAN_POSTGRES_MIGRATION.md` (overall plan)

## Summary

✅ Test database: PostgreSQL 16 with pgvector on port 5433  
✅ Test markers: migration, unit, integration, contract, perf  
✅ Fake embeddings: Fast, deterministic, 384-dim  
✅ Data seeding: Factory functions for all models  
✅ Pytest fixtures: db_session, uow, seed_conversations, toggle_postgres_mode  
✅ Test data: Real ChatGPT & Claude conversation samples  
✅ Directory structure: Organized for all test types  

**Phase 1.0 Status: COMPLETE** 🎉

Ready for Phase 1.1: API Contract Compliance Tests!
