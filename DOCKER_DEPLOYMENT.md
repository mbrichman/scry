# Docker Deployment Guide

## Overview

This guide covers deploying the fully containerized Dovos application stack, including:
- **dovos-rag-api**: Flask application with RAG capabilities
- **PostgreSQL 16**: Database with pgvector extension
- **Docker volumes**: Persistent data storage
- **Docker network**: Isolated container networking

## Prerequisites on Mac Mini

1. Docker installed (`brew install docker` or Docker Desktop)
2. `.env` file configured with PostgreSQL credentials
3. (Optional) Existing PostgreSQL data to migrate

## Quick Start

### 1. Prepare Environment File

```bash
cp .env.example .env
nano .env  # Edit with production values
```

**Required settings:**
```env
# PostgreSQL credentials (used by both postgres and dovos-rag services)
POSTGRES_USER=dovos
POSTGRES_PASSWORD=your-secure-password-here
POSTGRES_DB=dovos

# Application settings
USE_PG_SINGLE_STORE=true
OPENWEBUI_URL=http://your-openwebui-url:3000
OPENWEBUI_API_KEY=your-api-key
SECRET_KEY=generate-a-secure-random-key
```

**Note:** The `DATABASE_URL` is automatically constructed in docker-compose.yml using the PostgreSQL credentials.

### 2. Build and Start

```bash
# Build the images
docker compose build

# Start all services (PostgreSQL + Application)
docker compose up -d

# View logs
docker compose logs -f

# View logs for specific service
docker compose logs -f postgres
docker compose logs -f dovos-rag
```

**First-time setup:** The PostgreSQL container will automatically:
1. Initialize the database with the specified credentials
2. Run initialization scripts from `init-scripts/` directory
3. Create the pgvector extension
4. Be ready for the application to run Alembic migrations

### 3. Run Database Migrations

```bash
# Run Alembic migrations inside the application container
docker compose exec dovos-rag alembic upgrade head
```

### 4. Verify Running

```bash
# Check container status
docker compose ps

# Verify PostgreSQL is healthy
docker compose exec postgres pg_isready -U dovos

# Verify pgvector extension
docker compose exec postgres psql -U dovos -d dovos -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Test application endpoint
curl http://localhost:5001/api/rag/query -X POST \
  -H 'Content-Type: application/json' \
  -d '{"query": "test", "context_window": 3}'
```

## Service Management

### Start Service
```bash
docker compose up -d
```

### Stop Service
```bash
docker compose down
```

### Restart Service
```bash
docker compose restart
```

### View Logs
```bash
# Follow logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100
```

### Update to Latest Code

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose up -d --build
```

## Troubleshooting

### Container won't start
```bash
# Check logs for errors
docker compose logs

# Check container status
docker compose ps
```

### Database connection issues
```bash
# Check if PostgreSQL container is running
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# Test connection from application container
docker compose exec dovos-rag python -c "from db.database import test_connection; print('✅ PostgreSQL OK' if test_connection() else '❌ Connection failed')"
```

### Port already in use
```bash
# Find what's using port 5001
lsof -i :5001

# Stop conflicting service or change port in docker-compose.yml
```

### Rebuild from scratch
```bash
# Stop and remove containers (preserves volumes)
docker compose down

# Remove containers AND volumes (⚠️  deletes all data)
docker compose down -v

# Rebuild without cache
docker compose build --no-cache

# Start fresh
docker compose up -d
```

## Data Management

### PostgreSQL Data Persistence

PostgreSQL data is stored in a Docker named volume (`dovos_postgres_data`). This volume persists even when containers are stopped or removed.

```bash
# List Docker volumes
docker volume ls | grep dovos

# Inspect volume details
docker volume inspect dovos_postgres_data

# Check volume size
docker system df -v | grep dovos_postgres_data
```

### Backup Database

```bash
# Create backup directory
mkdir -p ./backups

# Backup database to file
docker compose exec -T postgres pg_dump -U dovos -d dovos > ./backups/dovos_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with custom format (compressed, allows selective restore)
docker compose exec -T postgres pg_dump -U dovos -d dovos -Fc > ./backups/dovos_backup_$(date +%Y%m%d_%H%M%S).dump
```

### Restore Database

```bash
# Restore from SQL file
docker compose exec -T postgres psql -U dovos -d dovos < ./backups/dovos_backup.sql

# Restore from custom format
docker compose exec -T postgres pg_restore -U dovos -d dovos -c /path/to/backup.dump

# Or copy backup into container first
docker cp ./backups/dovos_backup.dump dovos-postgres:/tmp/
docker compose exec postgres pg_restore -U dovos -d dovos -c /tmp/dovos_backup.dump
```

### Migrate Data from Host PostgreSQL

See `docs/DOCKER_DATA_MIGRATION.md` for detailed instructions on migrating existing data from host PostgreSQL to the containerized version.

## Advanced Configuration

### Custom PostgreSQL Port

To use a different host port for PostgreSQL:

```yaml
# In docker-compose.yml, change:
ports:
  - "5433:5432"  # Host port 5433 maps to container port 5432
```

### Using External PostgreSQL

If you want to use PostgreSQL on the host or another server:

1. Remove the `postgres` service from docker-compose.yml
2. Set `DATABASE_URL` environment variable in `.env`:
   ```env
   DATABASE_URL=postgresql+psycopg://user:pass@host.docker.internal:5432/dovos
   ```
3. Remove the `depends_on` section from dovos-rag service

### Resource Limits

Add to service configuration:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

## Production Checklist

- [ ] `.env` file configured with production values
- [ ] `SECRET_KEY` set to secure random value
- [ ] `DATABASE_URL` points to correct PostgreSQL instance
- [ ] PostgreSQL accessible from Docker container
- [ ] Docker service starts automatically on boot
- [ ] Logs directory mounted for persistence
- [ ] Endpoint accessible from OpenWebUI server
- [ ] OpenWebUI tool updated with Mac Mini IP

## Auto-Start on Boot

Docker will automatically restart containers unless stopped manually (`restart: unless-stopped` in compose file).

To ensure Docker itself starts on boot:

```bash
# macOS (if using Docker Desktop)
# Docker Desktop > Settings > General > "Start Docker Desktop when you log in"

# Or use system service
brew services start docker
```

## Monitoring

### Container Stats
```bash
docker stats dovos-rag-api
```

### Disk Usage
```bash
docker system df
```

### Clean Up Old Images
```bash
docker image prune -a
```
