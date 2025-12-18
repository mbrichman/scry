# DovOS MCP Server - MCPO Integration

Configuration guide for connecting DovOS MCP server to OpenWebUI via MCPO (MCP Orchestrator).

## Architecture

```
┌─────────────────────────┐
│   OpenWebUI Container   │
│                         │
└───────────┬─────────────┘
            │
            │ HTTP/REST API
            │
            ▼
┌─────────────────────────┐
│   MCPO Container        │
│   (MCP Orchestrator)    │
└───────────┬─────────────┘
            │
            │ HTTP/SSE (MCP Protocol)
            │
            ▼
┌─────────────────────────┐
│  DovOS MCP Server       │
│  http://dovos-mcp:8001  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  PostgreSQL Container   │
└─────────────────────────┘
```

## What is MCPO?

MCPO (MCP Orchestrator) is a proxy service that:
- Manages connections to multiple MCP servers
- Routes requests from OpenWebUI to appropriate MCP servers
- Handles authentication and authorization
- Provides unified API for OpenWebUI to access MCP tools

## Prerequisites

1. DovOS MCP server running (HTTP/SSE mode)
2. MCPO container running
3. All containers on same Docker network (or network connectivity)
4. OpenWebUI configured to use MCPO

## Configuration

### 1. Add DovOS MCP to docker-compose.yml

Ensure all services are on the same network:

```yaml
services:
  # PostgreSQL (existing)
  postgres:
    image: pgvector/pgvector:pg17
    container_name: dovos-postgres
    networks:
      - dovos-network
    # ... other config

  # DovOS MCP Server (existing)
  dovos-mcp:
    build:
      context: .
      dockerfile: dovos_mcp/Dockerfile
    container_name: dovos-mcp-server
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+psycopg://dovos:dovos_password@postgres:5432/dovos
      - PGAPPNAME=dovos-mcp-server
    networks:
      - dovos-network
    # ... other config

  # MCPO (add this)
  mcpo:
    image: ghcr.io/opencodeai/mcpo:latest  # Or your MCPO image
    container_name: mcpo
    ports:
      - "8000:8000"  # MCPO API port
    environment:
      - MCPO_CONFIG=/app/config/mcpo.json
    volumes:
      - ./mcpo-config.json:/app/config/mcpo.json:ro
    networks:
      - dovos-network
    depends_on:
      - dovos-mcp
    restart: unless-stopped

  # OpenWebUI (if running together)
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: openwebui
    ports:
      - "3000:8080"
    environment:
      - MCPO_URL=http://mcpo:8000  # Point to MCPO
    networks:
      - dovos-network
    depends_on:
      - mcpo
    restart: unless-stopped

networks:
  dovos-network:
    name: dovos_network
    driver: bridge
```

### 2. Create MCPO Configuration File

Create `mcpo-config.json` in your DovOS project root:

```json
{
  "version": "1.0",
  "servers": {
    "dovos": {
      "name": "DovOS Conversation Archive",
      "description": "Search and retrieve conversation history with iterative research capabilities",
      "url": "http://dovos-mcp-server:8001/sse",
      "transport": "sse",
      "enabled": true,
      "authentication": {
        "type": "none"
      },
      "metadata": {
        "category": "knowledge",
        "tags": ["conversations", "search", "rag", "archive"]
      }
    }
  },
  "settings": {
    "log_level": "info",
    "enable_cors": true,
    "allowed_origins": ["*"],
    "timeout": 30,
    "max_retries": 3
  }
}
```

### 3. Alternative: MCPO Environment Variable Configuration

If MCPO supports environment-based configuration:

```yaml
mcpo:
  image: ghcr.io/opencodeai/mcpo:latest
  environment:
    - MCP_SERVERS={"dovos":{"url":"http://dovos-mcp-server:8001/sse","transport":"sse","name":"DovOS Archive"}}
    - MCPO_LOG_LEVEL=info
    - MCPO_ENABLE_CORS=true
```

### 4. Configure OpenWebUI to Use MCPO

In OpenWebUI's configuration or environment:

```bash
# Environment variable
MCPO_URL=http://mcpo:8000

# Or in OpenWebUI's settings
ENABLE_MCP=true
MCP_ORCHESTRATOR_URL=http://mcpo:8000
```

## Deployment Steps

### Step 1: Start DovOS Infrastructure

```bash
# Start PostgreSQL and DovOS services
docker-compose up -d postgres dovos-rag dovos-mcp

# Wait for services to be healthy
docker ps
docker logs dovos-mcp-server
```

### Step 2: Verify DovOS MCP Server

```bash
# Test health endpoint
curl http://localhost:8001/health

# Expected: {"status": "ok", "service": "dovos-mcp"}
```

### Step 3: Create MCPO Configuration

```bash
# Create config file
cat > mcpo-config.json <<'EOF'
{
  "version": "1.0",
  "servers": {
    "dovos": {
      "name": "DovOS Conversation Archive",
      "url": "http://dovos-mcp-server:8001/sse",
      "transport": "sse",
      "enabled": true
    }
  }
}
EOF
```

### Step 4: Start MCPO

```bash
# Start MCPO service
docker-compose up -d mcpo

# Check MCPO logs
docker logs -f mcpo

# Test MCPO health
curl http://localhost:8000/health

# List registered MCP servers
curl http://localhost:8000/servers
# Should show: {"servers": ["dovos"]}
```

### Step 5: Start/Configure OpenWebUI

```bash
# If running OpenWebUI in Docker
docker-compose up -d openwebui

# Or configure existing OpenWebUI to point to MCPO
# Set: MCPO_URL=http://mcpo:8000
```

### Step 6: Test End-to-End

In OpenWebUI, ask:
```
"Search my conversations for Docker"
```

Check logs to verify the flow:

```bash
# OpenWebUI → MCPO
docker logs openwebui | grep -i mcp

# MCPO → DovOS MCP
docker logs mcpo | grep -i dovos

# DovOS MCP → Search
docker logs dovos-mcp-server | grep "Searching conversations"
```

## Network Topology

### Option 1: All on Same Network (Recommended)

```
dovos_network (bridge)
├── postgres (dovos-postgres)
├── dovos-mcp (dovos-mcp-server:8001)
├── mcpo (mcpo:8000)
└── openwebui (openwebui:8080)
```

**Benefits:**
- Fast communication
- No port exposure needed
- Secure internal networking

### Option 2: MCPO as Bridge Between Networks

```
openwebui_network          dovos_network
├── openwebui         ←→   mcpo   ←→   dovos-mcp
                                        postgres
```

**MCPO connected to both networks:**
```yaml
mcpo:
  networks:
    - openwebui_network
    - dovos_network

networks:
  openwebui_network:
    external: true
  dovos_network:
    external: true
```

## MCPO API Examples

### List Available MCP Servers

```bash
curl http://localhost:8000/servers
```

Response:
```json
{
  "servers": [
    {
      "id": "dovos",
      "name": "DovOS Conversation Archive",
      "enabled": true,
      "tools": [
        "search_conversations",
        "fetch_conversation"
      ]
    }
  ]
}
```

### List Available Tools

```bash
curl http://localhost:8000/tools
```

Response:
```json
{
  "tools": [
    {
      "server": "dovos",
      "name": "search_conversations",
      "description": "Search DovOS conversation archive..."
    },
    {
      "server": "dovos",
      "name": "fetch_conversation",
      "description": "Fetch complete conversation content..."
    }
  ]
}
```

### Execute Tool via MCPO

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "server": "dovos",
    "tool": "search_conversations",
    "arguments": {
      "query": "docker networking",
      "limit": 5
    }
  }'
```

## Troubleshooting

### MCPO Can't Connect to DovOS MCP

**Test from MCPO container:**
```bash
docker exec -it mcpo curl http://dovos-mcp-server:8001/health
```

**If fails:**
1. Check both containers are on same network:
   ```bash
   docker network inspect dovos_network
   ```

2. Check container name is correct:
   ```bash
   docker ps | grep dovos-mcp
   # Should show: dovos-mcp-server
   ```

3. Check MCP server is running:
   ```bash
   docker logs dovos-mcp-server
   ```

### OpenWebUI Can't Connect to MCPO

**Test from OpenWebUI container:**
```bash
docker exec -it openwebui curl http://mcpo:8000/health
```

**If fails:**
1. Verify MCPO_URL environment variable
2. Check MCPO is running: `docker logs mcpo`
3. Verify network connectivity

### Tools Not Appearing in OpenWebUI

1. **Check MCPO registered the DovOS server:**
   ```bash
   curl http://localhost:8000/servers
   # Should list "dovos"
   ```

2. **Check MCPO config file:**
   ```bash
   docker exec mcpo cat /app/config/mcpo.json
   ```

3. **Restart MCPO to reload config:**
   ```bash
   docker-compose restart mcpo
   ```

4. **Check OpenWebUI is configured for MCPO:**
   ```bash
   docker exec openwebui env | grep MCPO
   ```

### Search Returns No Results

**Test directly on MCP server:**
```bash
# Bypass MCPO for testing
docker exec -it dovos-mcp-server python -c "
from db.services.search_service import SearchService, SearchConfig
service = SearchService(SearchConfig())
results = service.search('test', limit=5)
print(f'Found {len(results)} results')
"
```

**Test via MCPO:**
```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"server":"dovos","tool":"search_conversations","arguments":{"query":"test"}}'
```

## Security Configuration

### Add Authentication to MCPO

If MCPO supports authentication:

```json
{
  "servers": {
    "dovos": {
      "url": "http://dovos-mcp-server:8001/sse",
      "authentication": {
        "type": "bearer",
        "token": "${DOVOS_MCP_TOKEN}"
      }
    }
  },
  "security": {
    "require_auth": true,
    "api_keys": [
      "${MCPO_API_KEY}"
    ]
  }
}
```

### Network Isolation

```yaml
# Separate networks for isolation
networks:
  frontend:  # OpenWebUI only
  backend:   # MCPO + MCP servers
  data:      # MCP servers + PostgreSQL

services:
  openwebui:
    networks:
      - frontend

  mcpo:
    networks:
      - frontend  # Talk to OpenWebUI
      - backend   # Talk to MCP servers

  dovos-mcp:
    networks:
      - backend   # Talk to MCPO
      - data      # Talk to PostgreSQL

  postgres:
    networks:
      - data      # Only accessible by MCP servers
```

## Monitoring

### Health Checks

```bash
# Check full chain
curl http://localhost:8000/health        # MCPO
curl http://localhost:8001/health        # DovOS MCP
curl http://localhost:5001/api/stats     # DovOS RAG API
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific services
docker logs -f openwebui
docker logs -f mcpo
docker logs -f dovos-mcp-server

# Follow a request through the chain
docker logs -f mcpo | grep dovos &
docker logs -f dovos-mcp-server | grep "Searching" &
# Then make a request in OpenWebUI
```

### Metrics

```bash
# Container stats
docker stats openwebui mcpo dovos-mcp-server

# MCPO metrics (if supported)
curl http://localhost:8000/metrics
```

## Complete Example docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: pgvector/pgvector:pg17
    container_name: dovos-postgres
    environment:
      - POSTGRES_USER=dovos
      - POSTGRES_PASSWORD=dovos_password
      - POSTGRES_DB=dovos
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - dovos-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dovos"]
      interval: 10s
      timeout: 5s
      retries: 5

  # DovOS RAG API
  dovos-rag:
    image: ghcr.io/mbrichman/dovos:main
    container_name: dovos-rag-api
    ports:
      - "5001:5001"
    environment:
      - DATABASE_URL=postgresql+psycopg://dovos:dovos_password@postgres:5432/dovos
    networks:
      - dovos-network
    depends_on:
      postgres:
        condition: service_healthy

  # DovOS MCP Server
  dovos-mcp:
    build:
      context: .
      dockerfile: dovos_mcp/Dockerfile
    container_name: dovos-mcp-server
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql+psycopg://dovos:dovos_password@postgres:5432/dovos
      - PGAPPNAME=dovos-mcp-server
    networks:
      - dovos-network
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8001/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3

  # MCPO (MCP Orchestrator)
  mcpo:
    image: ghcr.io/opencodeai/mcpo:latest
    container_name: mcpo
    ports:
      - "8000:8000"
    environment:
      - MCPO_CONFIG=/config/mcpo.json
    volumes:
      - ./mcpo-config.json:/config/mcpo.json:ro
    networks:
      - dovos-network
    depends_on:
      - dovos-mcp
    restart: unless-stopped

  # OpenWebUI
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: openwebui
    ports:
      - "3000:8080"
    environment:
      - MCPO_URL=http://mcpo:8000
      - ENABLE_MCP=true
    volumes:
      - openwebui_data:/app/backend/data
    networks:
      - dovos-network
    depends_on:
      - mcpo
    restart: unless-stopped

networks:
  dovos-network:
    name: dovos_network
    driver: bridge

volumes:
  postgres_data:
  openwebui_data:
```

## Quick Reference Commands

```bash
# Start everything
docker-compose up -d

# Check all services are running
docker-compose ps

# Test the chain
curl http://localhost:8000/servers  # MCPO lists DovOS
curl http://localhost:8001/health   # DovOS MCP healthy

# View logs
docker-compose logs -f mcpo dovos-mcp

# Restart after config changes
docker-compose restart mcpo

# Stop everything
docker-compose down
```

## Next Steps

1. ✅ Ensure DovOS MCP server is running on HTTP/SSE mode
2. ✅ Deploy MCPO container
3. ✅ Create MCPO configuration with DovOS server
4. ✅ Connect OpenWebUI to MCPO
5. ✅ Test end-to-end connectivity
6. 📊 Monitor logs to verify request flow
7. 🔍 Test search queries in OpenWebUI

---

**See also:**
- [DOCKER_NETWORK_DEPLOYMENT.md](DOCKER_NETWORK_DEPLOYMENT.md) - Docker networking details
- [PROMPTING_GUIDE.md](PROMPTING_GUIDE.md) - Optimize LLM iteration behavior
- [README.md](README.md) - Complete MCP server documentation
