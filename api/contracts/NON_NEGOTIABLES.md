# API Contract Non-Negotiables

This document defines the absolute requirements that **MUST NOT CHANGE** during the backend migration to ensure frontend compatibility.

## 🚨 CRITICAL: Breaking any of these contracts will break the frontend!

### HTTP Routes and Methods

These exact routes and methods must be preserved:

#### HTML Pages (Server-Side Rendered)
- `GET /` - Redirect to conversations view
- `GET /conversations` - HTML conversations list page
- `POST /conversations` - HTML conversations list page with search
- `GET /conversations/<page>` - HTML conversations list page (paginated)
- `POST /conversations/<page>` - HTML conversations list page (paginated with search)
- `GET /view/<doc_id>` - HTML conversation detail view
- `GET /export/<doc_id>` - Export conversation as markdown file
- `GET /upload` - HTML upload form
- `POST /upload` - File upload handler
- `GET /stats` - HTML stats page

#### JSON API Endpoints
- `GET /api/conversations` - JSON conversations list
- `GET /api/conversation/<conversation_id>` - JSON conversation detail
- `GET /api/search` - JSON search results
- `GET /api/stats` - JSON system statistics
- `POST /api/rag/query` - RAG query endpoint
- `GET /api/rag/health` - RAG health check
- `POST /export_to_openwebui/<doc_id>` - Export to OpenWebUI
- `POST /clear_db` - Clear database

### Query Parameters

These query parameters must be supported exactly as documented:

#### GET /api/conversations
- `page` (optional, integer, default 1) - Page number (1-based)
- `limit` (optional, integer, default 50, max 100) - Items per page

#### GET /api/search  
- `q` (required, string) - Search query
- `n` (optional, integer, default 5) - Number of results
- `keyword` (optional, boolean, default false) - Use keyword search instead of semantic

#### GET /api/conversation/<conversation_id>
- No query parameters

#### POST /api/rag/query
- Request body JSON only (no query parameters)

### Response Schema Requirements

#### Field Names and Types
All response field names, types, and nullability must be preserved exactly:

**ConversationSummaryModel:**
```json
{
  "id": "string (required)",
  "title": "string (required)", 
  "preview": "string (required, max 200 chars)",
  "date": "string (required, empty string if unknown)",
  "source": "string (required)"
}
```

**ConversationsListResponse:**
```json
{
  "conversations": ["array of ConversationSummaryModel (required)"],
  "pagination": {
    "page": "integer (required, 1-based)",
    "limit": "integer (required)",
    "total": "integer (required)", 
    "has_next": "boolean (required)",
    "has_prev": "boolean (required)"
  }
}
```

**MessageModel:**
```json
{
  "id": "string (required, format: 'user-1', 'assistant-2', etc.)",
  "role": "string (required, values: 'user', 'assistant', 'system')",
  "content": "string (required)",
  "timestamp": "string or null (optional)"
}
```

**ConversationDetailResponse:**
```json
{
  "id": "string (required)",
  "title": "string (required)",
  "source": "string (required)",
  "date": "string or null (optional)",
  "assistant_name": "string (required, e.g. 'ChatGPT', 'Claude', 'AI')",
  "messages": ["array of MessageModel (required)"]
}
```

### HTTP Status Codes

These exact status codes must be returned:

- `200` - Success for all successful GET/POST operations
- `400` - Bad Request (missing required parameters)
- `404` - Not Found (conversation not found)
- `500` - Internal Server Error

### Error Response Format

All error responses must use this exact format:
```json
{
  "error": "string (required, human-readable error message)"
}
```

### Pagination Semantics

The pagination must work exactly as currently implemented:
- Page numbers are 1-based (not 0-based)
- `has_next` is `true` if there are more pages after the current one
- `has_prev` is `true` if the current page is greater than 1
- `total` is the total count of all items (not pages)

### Content Preview Rules

- Conversation previews: Max 200 characters, markdown stripped, truncated at word boundaries with "..."
- Search result content: Max 300 characters, same formatting rules
- RAG result preview: Max 500 characters, same formatting rules

### Search Result Distance/Relevance

- `distance`: Float representing distance from query (lower = more relevant)
- `relevance`: Float calculated as `1.0 - distance` (higher = more relevant)
- Range: Both should be between 0.0 and 1.0

### Message ID Format

Message IDs must follow these patterns:
- User messages: `"user-1"`, `"user-2"`, etc.
- Assistant messages: `"assistant-1"`, `"assistant-2"`, etc.
- Sequential numbering within each conversation

### Assistant Name Mapping

Based on source field:
- `"chatgpt"` → `"ChatGPT"`
- `"claude"` → `"Claude"`  
- Other/unknown → `"AI"`

### Date Format Expectations

- ISO 8601 format preferred: `"2025-01-15T14:30:22Z"`
- Alternative format accepted: `"2025-01-15 14:30:22"`
- Empty string `""` for unknown dates (not `null`)
- `null` allowed only where explicitly marked as optional

## Testing Requirements

Before any deployment:

1. **Contract Tests Must Pass**: All tests in `tests/test_api_contracts.py` must pass
2. **Golden Response Validation**: All golden responses must validate against schemas
3. **Integration Tests**: Manual testing of key frontend workflows
4. **Backwards Compatibility**: Existing API clients must continue to work without changes

## Rollback Requirements

The feature flag system must allow immediate rollback:
- Set `USE_PG_SINGLE_STORE=false` → immediate revert to legacy system  
- No data migration or schema changes required for rollback
- Frontend continues working without any changes

## Documentation

When implementing new backend:
- Map internal data structures to these exact response formats using `api/compat.py`
- Validate all responses against `api/contracts/api_contract.py`
- Test against golden responses in `api/contracts/golden_responses.py`
- Never modify these contracts without explicit frontend team approval

---

**⚠️  REMEMBER: The frontend depends on these exact contracts. Changes will cause breakage!**