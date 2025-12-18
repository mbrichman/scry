# DovOS MCP Server

Model Context Protocol (MCP) server for DovOS, enabling LLMs to autonomously search and explore your conversation archive with iterative, Perplexity-style research capabilities.

## Overview

The DovOS MCP server exposes two powerful tools that allow LLMs to:

1. **Search** the conversation archive using hybrid semantic + keyword search
2. **Fetch** complete conversation content by ID
3. **Iterate** on searches based on findings to build comprehensive answers

This enables autonomous research workflows where the LLM can explore your conversation history intelligently, rather than relying on a single search query.

## Tools

### `search_conversations`

Search the DovOS conversation archive using hybrid semantic + keyword search.

**Parameters:**
- `query` (required): Search query in natural language or keywords
- `limit` (optional): Maximum results to return (1-50, default: 10)
- `search_mode` (optional): Search strategy
  - `hybrid` (default): Combines semantic + keyword search (best results)
  - `vector`: Semantic similarity only (best for conceptual queries)
  - `fulltext`: Keyword search only (best for exact terms)

**Returns:**
- List of matching conversations with:
  - Conversation ID (for fetching)
  - Title
  - Relevance score
  - Message count
  - Content preview/snippet

**Example usage pattern:**
```
LLM: "I need to find conversations about authentication implementation"
→ search_conversations(query="authentication implementation", limit=5)
→ Reviews snippets, identifies 2 promising conversations
→ fetch_conversation(conversation_id="abc-123")
→ fetch_conversation(conversation_id="def-456")
→ Synthesizes findings from both conversations
```

### `fetch_conversation`

Retrieve complete conversation content by ID.

**Parameters:**
- `conversation_id` (required): UUID from search results

**Returns:**
- Full conversation with:
  - Title and metadata
  - All messages in chronological order
  - Message roles (user/assistant/system)
  - Timestamps

**Example:**
```
fetch_conversation(conversation_id="550e8400-e29b-41d4-a716-446655440000")
```

## Architecture

The MCP server leverages DovOS's existing infrastructure:

- **SearchService**: Hybrid search (PostgreSQL FTS + pgvector)
- **ConversationRepository**: Efficient data access with eager loading
- **DatabaseConnection**: Shared connection pool with main app

### Search Capabilities

**Hybrid Search (Default):**
- 60% semantic similarity (384-dim embeddings via sentence-transformers)
- 40% keyword relevance (PostgreSQL full-text search)
- Query expansion with synonyms
- Typo tolerance via trigram matching

**Vector Search:**
- Pure semantic similarity using pgvector
- Best for conceptual/thematic queries
- Language-agnostic

**Full-Text Search:**
- PostgreSQL `tsvector` with GIN indexes
- Best for exact terms, names, technical keywords
- Fast and efficient

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the `mcp` package along with other DovOS dependencies.

### 2. Configure Environment

Ensure your `.env` file has the required DovOS configuration:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dovos
# ... other DovOS settings
```

### 3. Verify Database

Ensure your PostgreSQL database is running with:
- `pgvector` extension enabled
- Embeddings generated for conversations
- DovOS schema applied

## Running the Server

### Deployment Modes

The MCP server supports two deployment modes:

**1. Stdio Mode (Local Development)**
- MCP server runs as subprocess spawned by OpenWebUI
- Communication via stdin/stdout
- Best for local development and testing

**2. Docker Network Mode (Production)**
- MCP server runs as standalone HTTP/SSE service in Docker
- Communication via HTTP over Docker network
- Best for containerized deployments

### Stdio Mode Setup

Run the MCP server directly:

```bash
python dovos_mcp/dovos_server.py
```

Or use the launcher script:

```bash
./dovos_mcp/run_server.sh
```

The server runs on stdio (standard input/output) per MCP specification.

### Docker Network Mode Setup

**For containerized deployments (DovOS + OpenWebUI in Docker):**

See **[DOCKER_NETWORK_DEPLOYMENT.md](dovos_mcp/DOCKER_NETWORK_DEPLOYMENT.md)** for complete guide.

Quick start:
```bash
# Start all services including MCP server
docker-compose up -d

# Verify MCP server is running
curl http://localhost:8001/health
```

### Integration with OpenWebUI

Configure OpenWebUI to connect to the DovOS MCP server:

1. **Add MCP Server to OpenWebUI Configuration**

   In your OpenWebUI settings or MCPO configuration, add:

   ```json
   {
     "mcpServers": {
       "dovos": {
         "command": "python",
         "args": ["/path/to/dovos/dovos_mcp/dovos_server.py"],
         "env": {
           "DATABASE_URL": "postgresql://user:password@localhost:5432/dovos"
         }
       }
     }
   }
   ```

2. **Restart OpenWebUI**

   The MCP server will be spawned automatically when OpenWebUI starts.

3. **Verify Connection**

   Check OpenWebUI logs for:
   ```
   DovOS MCP Server starting...
   Services initialized successfully
   MCP server running on stdio
   ```

## Usage Patterns

### Pattern 1: Iterative Research

```
User asks: "How did we implement rate limiting in our API?"

LLM workflow:
1. search_conversations("rate limiting API implementation")
2. Reviews 10 results, identifies 3 relevant conversations
3. fetch_conversation(conv_1) - reads full implementation discussion
4. fetch_conversation(conv_2) - reads troubleshooting thread
5. search_conversations("rate limiting Redis configuration")  # Follow-up
6. fetch_conversation(conv_3) - reads configuration details
7. Synthesizes comprehensive answer with references
```

### Pattern 2: Multi-Source Synthesis

```
User asks: "What are all the authentication methods we've discussed?"

LLM workflow:
1. search_conversations("authentication methods")
2. fetch_conversation() for top 5 results
3. search_conversations("OAuth implementation")  # Specific follow-up
4. search_conversations("JWT tokens")  # Another angle
5. Compiles comprehensive list from all fetched conversations
```

### Pattern 3: Clarification & Refinement

```
User asks: "Find that conversation about Docker"

LLM workflow:
1. search_conversations("Docker")  # Too broad, 50 results
2. Asks user: "I found 50 Docker-related conversations. Can you narrow it down?"
3. User: "Docker networking issues"
4. search_conversations("Docker networking issues")
5. fetch_conversation() for top 3 most relevant
6. Presents summaries for user to choose
```

## Testing

### Test Search Tool

```bash
# You can test the tools manually using MCP inspector or by calling directly
python -c "
from mcp.server import Server
# ... test code
"
```

### Integration Testing

When integrated with OpenWebUI, test by asking:
- "Search my conversations for X"
- "Find all discussions about Y"
- "What did we decide about Z?"

The LLM should autonomously use the MCP tools to explore and answer.

## Logging

The server logs to stdout at INFO level:

```
2025-12-16 10:30:00 - dovos - INFO - DovOS MCP Server starting...
2025-12-16 10:30:01 - dovos - INFO - Services initialized successfully
2025-12-16 10:30:01 - dovos - INFO - MCP server running on stdio
2025-12-16 10:30:15 - dovos - INFO - Searching conversations: query='authentication', mode=hybrid, limit=10
2025-12-16 10:30:16 - dovos - INFO - Fetching conversation: 550e8400-e29b-41d4-a716-446655440000
```

Errors are logged with full stack traces for debugging.

## Troubleshooting

### "No conversations found"

- Check that embeddings are generated: `GET /api/embedding/status`
- Verify database connection and schema
- Try different `search_mode` values

### "Conversation not found"

- Verify the conversation ID is valid UUID format
- Check that the conversation exists in the database
- Ensure conversation wasn't deleted

### "Database connection error"

- Verify `DATABASE_URL` in environment
- Check PostgreSQL is running and accessible
- Ensure `pgvector` extension is installed

### Performance Issues

- Check embedding coverage (embeddings improve search quality)
- Monitor PostgreSQL query performance
- Consider adding IVFFLAT index for large datasets (>100k messages)

## Architecture Notes

### Why Hybrid Search?

Hybrid search combines the best of both worlds:
- **Semantic search**: Understands meaning, handles synonyms, language variations
- **Keyword search**: Fast, precise for exact terms, technical keywords

This mirrors how humans search: sometimes we know exact terms, sometimes we describe concepts.

### Database Sharing

The MCP server shares the same PostgreSQL database as the main DovOS Flask app:
- No data duplication
- Real-time search over latest data
- Same connection pooling and optimization

### Stateless Design

Each tool call is independent:
- No session state between calls
- LLM manages conversation context
- Scales horizontally if needed

## Security Considerations

Since this MCP server is **not publicly exposed** and only callable from OpenWebUI:

- No authentication/authorization layer needed
- Relies on network isolation
- Trusted internal communication only
- All queries logged for audit trail

**Important:** Do not expose this MCP server to the public internet without adding proper authentication.

## Future Enhancements

Potential additions for future versions:

1. **Conversation filtering**: Filter by date range, source (Claude/ChatGPT), etc.
2. **Multi-conversation fetch**: Batch fetch multiple conversations in one call
3. **Message-level search**: Search and return individual messages, not just conversations
4. **Export tool**: Export search results or conversations to various formats
5. **Stats tool**: Get archive statistics (total conversations, date ranges, etc.)

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [DovOS Documentation](../docs/)
- [OpenWebUI MCP Integration](https://docs.openwebui.com/)

## License

Same as DovOS (see root LICENSE file).
