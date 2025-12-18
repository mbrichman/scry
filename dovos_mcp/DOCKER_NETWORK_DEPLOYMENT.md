# DovOS MCP Server - Docker Network Deployment

Guide for running the MCP server in a Docker container and connecting it to OpenWebUI over a Docker network.

## Architecture

```
┌─────────────────────────┐
│   OpenWebUI Container   │
│   (your existing OWUI)  │
└───────────┬─────────────┘
            │ HTTP/SSE
            │ (MCP Protocol)
            ▼
┌─────────────────────────┐
│  DovOS MCP Container    │
│  Port: 8001             │
│  Network: dovos_network │
└───────────┬─────────────┘
            │ PostgreSQL
            ▼
┌─────────────────────────┐
│  PostgreSQL Container   │
│  (pgvector enabled)     │
└─────────────────────────┘
```

## Prerequisites

1. DovOS is running in Docker (existing setup)
2. OpenWebUI is running in Docker (separate container)
3. Both containers can communicate over network

## Deployment Options

### Option 1: Same Docker Network (Recommended)

**Add OpenWebUI to DovOS network:**

```yaml
# In your OpenWebUI docker-compose.yml or docker run command
networks:
  - dovos_network

# External network reference
networks:
  dovos_network:
    external: true
```

**MCP Server URL from OpenWebUI:**
```
http://dovos-mcp-server:8001
```

### Option 2: Different Networks with Bridge

**Expose MCP port to host:**
Already configured in docker-compose.yml:
```yaml
ports:
  - "8001:8001"
```

**MCP Server URL from OpenWebUI:**
```
http://host.docker.internal:8001  # From OpenWebUI container
```

Or use the host machine's IP:
```
http://192.168.1.x:8001  # Replace with your IP
```

## Step-by-Step Setup

### 1. Start DovOS with MCP Server

```bash
cd /path/to/dovos

# Build and start all services (including new MCP server)
docker-compose up -d

# Verify MCP server is running
docker ps | grep dovos-mcp
docker logs dovos-mcp-server

# Check health
curl http://localhost:8001/health
# Should return: {"status": "ok", "service": "dovos-mcp"}
```

### 2. Configure OpenWebUI MCP Connection

OpenWebUI needs to know about the MCP server. The configuration depends on your OpenWebUI version.

#### For OpenWebUI with Native MCP Support

Add to OpenWebUI's MCP configuration file or environment:

**If on same network:**
```json
{
  "mcpServers": {
    "dovos": {
      "url": "http://dovos-mcp-server:8001/sse",
      "transport": "sse",
      "description": "DovOS conversation archive search and retrieval"
    }
  }
}
```

**If using host networking:**
```json
{
  "mcpServers": {
    "dovos": {
      "url": "http://host.docker.internal:8001/sse",
      "transport": "sse",
      "description": "DovOS conversation archive search and retrieval"
    }
  }
}
```

#### Environment Variable Method

```bash
# In OpenWebUI's docker-compose.yml or .env
MCP_SERVERS='{"dovos":{"url":"http://dovos-mcp-server:8001/sse","transport":"sse"}}'
```

### 3. Add OpenWebUI to DovOS Network

**Option A: Modify OpenWebUI's docker-compose.yml**

```yaml
services:
  openwebui:
    # ... existing config ...
    networks:
      - default  # OpenWebUI's own network
      - dovos_network  # Add DovOS network

networks:
  dovos_network:
    external: true
    name: dovos_network
```

**Option B: Docker run command**

```bash
docker run -d \
  --name openwebui \
  --network dovos_network \
  # ... other options ...
  ghcr.io/open-webui/open-webui:main
```

**Option C: Connect existing container**

```bash
docker network connect dovos_network openwebui
```

### 4. Verify Connection

From inside OpenWebUI container:
```bash
# Connect to OpenWebUI container
docker exec -it openwebui /bin/bash

# Test connectivity to MCP server
curl http://dovos-mcp-server:8001/health

# Should return: {"status": "ok", "service": "dovos-mcp"}
```

### 5. Test MCP Tools in OpenWebUI

Ask OpenWebUI:
```
"Search my conversations for Docker"
```

Check OpenWebUI logs to see MCP tool usage:
```bash
docker logs -f openwebui
```

Check MCP server logs to see requests:
```bash
docker logs -f dovos-mcp-server
```

## Complete docker-compose Example

If you want to run everything together:

```yaml
# docker-compose.full.yml
version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: pgvector/pgvector:pg17
    # ... (existing config from DovOS)

  # DovOS RAG API
  dovos-rag:
    image: ghcr.io/mbrichman/dovos:main
    # ... (existing config)

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
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - dovos-network

  # OpenWebUI
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: openwebui
    ports:
      - "3000:8080"
    environment:
      - MCP_SERVERS={"dovos":{"url":"http://dovos-mcp-server:8001/sse","transport":"sse"}}
    volumes:
      - openwebui_data:/app/backend/data
    networks:
      - dovos-network
    depends_on:
      - dovos-mcp

networks:
  dovos-network:
    name: dovos_network
    driver: bridge

volumes:
  postgres_data:
  openwebui_data:
```

## Troubleshooting

### MCP Server Won't Start

**Check logs:**
```bash
docker logs dovos-mcp-server
```

**Common issues:**
- Database connection error → Check DATABASE_URL environment variable
- Port already in use → Change port in docker-compose.yml
- Missing dependencies → Rebuild with `docker-compose build dovos-mcp`

### OpenWebUI Can't Reach MCP Server

**Test connectivity from OpenWebUI:**
```bash
docker exec -it openwebui curl http://dovos-mcp-server:8001/health
```

**If connection fails:**

1. **Check network:**
   ```bash
   docker network inspect dovos_network
   # Should show both openwebui and dovos-mcp-server
   ```

2. **Check container names:**
   ```bash
   docker ps | grep dovos-mcp
   # Should show dovos-mcp-server
   ```

3. **Try IP address instead:**
   ```bash
   # Get MCP server IP
   docker inspect dovos-mcp-server | grep IPAddress

   # Use IP in OpenWebUI config
   "url": "http://172.18.0.5:8001/sse"  # Use actual IP
   ```

### MCP Tools Not Appearing in OpenWebUI

1. **Check OpenWebUI MCP configuration:**
   - Ensure MCP_SERVERS environment variable is set
   - Or MCP config file is in correct location

2. **Check OpenWebUI version:**
   - MCP support requires OpenWebUI v0.3.0+
   - Update: `docker pull ghcr.io/open-webui/open-webui:main`

3. **Restart OpenWebUI:**
   ```bash
   docker restart openwebui
   ```

4. **Check OpenWebUI logs:**
   ```bash
   docker logs openwebui | grep -i mcp
   ```

### Search Returns No Results

1. **Check embeddings are generated:**
   ```bash
   curl http://localhost:5001/api/embedding/status
   ```

2. **Verify conversations exist:**
   ```bash
   curl http://localhost:5001/api/conversations
   ```

3. **Test search directly:**
   ```bash
   curl http://localhost:5001/api/search?q=test
   ```

## Network Modes Comparison

| Mode | MCP URL | Pros | Cons |
|------|---------|------|------|
| **Same Docker Network** | `http://dovos-mcp-server:8001` | ✅ Fast<br>✅ Secure<br>✅ No port exposure | ⚠️ Requires network config |
| **Host Port Mapping** | `http://host.docker.internal:8001` | ✅ Simple<br>✅ Works across networks | ⚠️ Exposes port<br>⚠️ Slower |
| **Host IP** | `http://192.168.1.x:8001` | ✅ Simple | ⚠️ IP may change<br>⚠️ Exposes port |

**Recommendation:** Use same Docker network for production.

## Security Considerations

### For Internal Use (Recommended)

Current setup is fine:
- No authentication needed
- Network isolation provides security
- Only accessible within Docker network

### For External/Multi-Tenant

If exposing outside Docker network:

1. **Add authentication:**
   - API key in headers
   - OAuth/JWT tokens
   - Network policies

2. **Use HTTPS:**
   - Add nginx reverse proxy
   - SSL/TLS certificates

3. **Rate limiting:**
   - Prevent abuse
   - Per-user quotas

## Monitoring

### Health Checks

**MCP Server:**
```bash
curl http://localhost:8001/health
```

**From OpenWebUI:**
```bash
docker exec openwebui curl http://dovos-mcp-server:8001/health
```

### Logs

**MCP Server logs:**
```bash
docker logs -f dovos-mcp-server

# Filter for searches
docker logs dovos-mcp-server | grep "Searching conversations"

# Filter for errors
docker logs dovos-mcp-server | grep ERROR
```

**OpenWebUI logs:**
```bash
docker logs -f openwebui | grep -i mcp
```

### Metrics

Check container stats:
```bash
docker stats dovos-mcp-server
```

## Performance Tuning

### For High Load

**Increase workers in http_server.py:**
```bash
# In docker-compose.yml, override CMD
command: >
  uvicorn dovos_mcp.http_server:app
  --host 0.0.0.0
  --port 8001
  --workers 4
  --loop asyncio
```

**Increase database connection pool:**
```python
# In db/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Increase from default
    max_overflow=40
)
```

### For Low Resources

**Reduce workers:**
```bash
command: >
  uvicorn dovos_mcp.http_server:app
  --host 0.0.0.0
  --port 8001
  --workers 1
```

## Next Steps

1. ✅ Start DovOS with MCP server
2. ✅ Add OpenWebUI to network
3. ✅ Configure OpenWebUI MCP connection
4. ✅ Test connectivity
5. ✅ Try search queries
6. 📈 Monitor performance
7. 🔒 Consider security hardening (if needed)

## Quick Reference

**Start everything:**
```bash
docker-compose up -d
```

**Check status:**
```bash
docker ps
curl http://localhost:8001/health
```

**View logs:**
```bash
docker logs -f dovos-mcp-server
```

**Restart MCP server:**
```bash
docker-compose restart dovos-mcp
```

**Rebuild after code changes:**
```bash
docker-compose build dovos-mcp
docker-compose up -d dovos-mcp
```

**Stop everything:**
```bash
docker-compose down
```
