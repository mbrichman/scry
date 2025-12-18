# DovOS MCP Server - Quick Start Guide

Get your MCP server running in 3 steps.

**Deployment modes:**
- **Stdio mode**: For local development when OpenWebUI spawns MCP as a subprocess
- **Docker + MCPO mode**: For production with OpenWebUI + MCPO + DovOS MCP in containers (recommended)
- **Docker direct mode**: For simple Docker deployments without MCPO

👉 **Using MCPO? See [MCPO_CONFIGURATION.md](MCPO_CONFIGURATION.md)**
👉 **Docker without MCPO? See [DOCKER_NETWORK_DEPLOYMENT.md](DOCKER_NETWORK_DEPLOYMENT.md)**

## Stdio Mode (Local Development)

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs the `mcp` package and all DovOS dependencies.

## 2. Test the Server

```bash
python dovos_mcp/test_server.py
```

You should see:
```
✓ MCP SDK imported successfully
✓ DovOS MCP server loaded: dovos
✓ DovOS services imported successfully
✓ All structural tests passed!
```

## 3. Configure in OpenWebUI (Stdio Mode)

**This is for stdio/subprocess mode only.**
For Docker deployments, see [DOCKER_NETWORK_DEPLOYMENT.md](DOCKER_NETWORK_DEPLOYMENT.md).

Add this to your OpenWebUI MCP configuration (location varies by installation):

```json
{
  "mcpServers": {
    "dovos": {
      "command": "python",
      "args": ["/Users/markrichman/projects/dovos/dovos_mcp/dovos_server.py"],
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/dovos",
        "PYTHONPATH": "/Users/markrichman/projects/dovos"
      },
      "description": "DovOS conversation archive search and retrieval"
    }
  }
}
```

**Replace:**
- `/Users/markrichman/projects/dovos` with your actual DovOS path
- Database URL with your PostgreSQL connection string

## Testing in OpenWebUI

Once configured, restart OpenWebUI and test by asking:

- "Search my conversations for authentication"
- "Find all discussions about Docker"
- "What did we talk about regarding API design?"

The LLM will autonomously use the MCP tools to search and fetch conversations.

## What the LLM Can Do

The MCP server gives the LLM two powerful tools:

**search_conversations** - Search your conversation archive
- Hybrid semantic + keyword search
- Returns conversation IDs, titles, scores, and previews
- Configurable search modes (hybrid/vector/fulltext)

**fetch_conversation** - Retrieve full conversation content
- Gets all messages in chronological order
- Complete with roles, timestamps, and content

**Iterative Research Pattern:**
1. LLM searches broadly → sees multiple results
2. LLM fetches promising conversations → reads full content
3. LLM refines search based on findings → discovers more
4. LLM synthesizes comprehensive answer from multiple sources

This enables Perplexity-style autonomous research over your conversation history!

## Troubleshooting

**"Module 'mcp' not found"**
- Run: `pip install mcp`

**"Database connection error"**
- Check PostgreSQL is running
- Verify DATABASE_URL in .env or config
- Ensure database has DovOS schema applied

**"No conversations found"**
- Check embeddings are generated: `curl http://localhost:5000/api/embedding/status`
- Try different search modes: hybrid/vector/fulltext

## Next Steps

See the full documentation in `dovos_mcp/README.md` for:
- Detailed architecture
- Search capabilities explained
- Advanced configuration options
- Security considerations
- Future enhancements
