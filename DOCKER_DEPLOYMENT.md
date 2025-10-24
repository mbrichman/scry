# Docker Deployment Guide

## Prerequisites on Mac Mini

1. Docker installed (`brew install docker` or Docker Desktop)
2. PostgreSQL running on host (not in Docker)
3. `.env` file configured

## Quick Start

### 1. Prepare Environment File

```bash
cp .env.example .env
nano .env  # Edit with production values
```

**Required settings:**
- `USE_PG_SINGLE_STORE=true`
- `DATABASE_URL=postgresql+psycopg://user:pass@host.docker.internal:5432/dovos_prod`
- `OPENWEBUI_URL=http://your-openwebui-url:3000`
- `OPENWEBUI_API_KEY=your-api-key`
- `SECRET_KEY=generate-a-secure-random-key`

**Note:** Use `host.docker.internal` in `DATABASE_URL` to connect to PostgreSQL on the host machine.

### 2. Build and Start

```bash
# Build the image
docker compose build

# Start the service
docker compose up -d

# View logs
docker compose logs -f
```

### 3. Verify Running

```bash
# Check container status
docker compose ps

# Test endpoint
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
- Verify PostgreSQL is running: `pg_isready`
- Check `DATABASE_URL` uses `host.docker.internal` for host PostgreSQL
- Ensure PostgreSQL allows connections from Docker network

### Port already in use
```bash
# Find what's using port 5001
lsof -i :5001

# Stop conflicting service or change port in docker-compose.yml
```

### Rebuild from scratch
```bash
# Remove containers and volumes
docker compose down -v

# Rebuild without cache
docker compose build --no-cache

# Start fresh
docker compose up -d
```

## Advanced Configuration

### Using External PostgreSQL Network

If you need specific networking:

```yaml
# In docker-compose.yml, replace network_mode: host with:
networks:
  - dovos-network

networks:
  dovos-network:
    driver: bridge
```

### Adding Health Checks

Uncomment the healthcheck section in `docker-compose.yml` to enable automatic container health monitoring.

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
