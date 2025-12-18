# DovOS MCP Server - Prompting Guide

How to get the best iteration behavior from your LLM using the DovOS MCP tools.

## Understanding the Design

The MCP server provides **tools**, not **strategy**. The LLM decides:
- When to search vs. fetch
- How many times to iterate
- Which results look promising
- When it has enough information

**You control this through prompting.**

## 1. System Prompt Configuration (Recommended)

Add this to your OpenWebUI system prompt or custom instructions:

```markdown
## Conversation Archive Research Protocol

When answering questions about past conversations using the DovOS MCP tools:

### Search Strategy
1. **Start broad** - Use general terms to see what's available
2. **Review carefully** - Read snippets and scores before fetching
3. **Fetch strategically** - Get 2-5 of the most relevant conversations
4. **Iterate based on findings** - Do follow-up searches for:
   - Specific concepts you discovered
   - Related topics mentioned
   - Alternative terminology
5. **Try different search modes** when appropriate:
   - `hybrid` (default): Best for general queries
   - `vector`: Best for conceptual/thematic queries
   - `fulltext`: Best for exact terms, names, technical keywords

### Quality Standards
- Don't settle for a single search result
- Fetch multiple conversations to get comprehensive coverage
- If the first search doesn't fully answer the question, refine your search
- Cite conversation IDs in your answer
- Synthesize findings from multiple sources

### Example Pattern
```
User asks: "What did we discuss about authentication?"

Your approach:
1. search_conversations("authentication", limit=10)
2. Review results - notice OAuth, JWT, and session-based auth mentioned
3. fetch_conversation for top 3 results
4. search_conversations("OAuth implementation") - follow-up
5. fetch_conversation for 2 more relevant results
6. Synthesize comprehensive answer with citations
```

Treat this like research, not a simple keyword search.
```

## 2. User Prompt Patterns

### ❌ Basic Prompts (Less Effective)

These may only trigger one search:
```
"What did we talk about Docker?"
"Find authentication conversations"
"Show me API discussions"
```

### ✅ Research-Oriented Prompts (More Effective)

These encourage iteration:
```
"Research my conversation history thoroughly and tell me everything
we've discussed about Docker. Look at multiple conversations and
cover all aspects - setup, networking, debugging, etc."

"I need a comprehensive summary of all authentication-related
discussions. Search broadly, then drill into specific methods
(OAuth, JWT, sessions, etc.) that you discover."

"Explore my conversations about API design patterns. Start with
a general search, fetch the most relevant ones, then search for
specific patterns mentioned (REST, GraphQL, RPC, etc.)."
```

### ✅ Explicit Step-by-Step (Most Effective)

Give the LLM a research plan:
```
"I need you to research my conversations about database optimization.
Follow these steps:

1. Search broadly for 'database optimization'
2. Fetch the top 5 results
3. Identify specific techniques mentioned (indexing, caching, etc.)
4. Search for each technique specifically
5. Fetch 2-3 conversations per technique
6. Create a comprehensive guide with examples from my conversations
7. Include conversation IDs as citations"
```

## 3. Query Modifiers

Add these phrases to encourage better behavior:

**Comprehensiveness:**
- "Search thoroughly..."
- "Give me a complete picture..."
- "Look at multiple conversations..."
- "Don't just use the first result..."

**Iteration:**
- "Start broad, then drill down..."
- "Do follow-up searches for..."
- "Explore related topics..."
- "Keep searching until you have a full understanding..."

**Quality:**
- "Cite your sources..."
- "Include conversation IDs..."
- "Synthesize from multiple conversations..."
- "Cross-reference findings..."

## 4. Advanced Techniques

### Chain of Thought + MCP

Encourage explicit reasoning:
```
"Think through this step-by-step:
1. What search terms would find relevant conversations?
2. What do the search results tell you?
3. Which conversations should you fetch?
4. What new terms did you discover?
5. What follow-up searches are needed?
6. Do you have enough information now?"
```

### Comparative Analysis

Force multiple iterations:
```
"Compare how we've approached authentication in different projects.
You'll need to search for authentication generally, then search for
each project name you discover, and synthesize the differences."
```

### Progressive Refinement

```
"Start with a broad search for 'API design'. Based on what you find,
search for specific patterns (REST, GraphQL, etc.). For each pattern,
search for implementation examples. Build a decision matrix showing
when we used each approach and why."
```

## 5. Example Scenarios

### Scenario: Researching a Technical Topic

**User:** "I'm working on implementing rate limiting. What have we discussed about this before?"

**Good LLM behavior with proper prompting:**
```
1. search_conversations("rate limiting", limit=10)
   → Finds 8 results

2. Reviews snippets, sees mentions of:
   - Redis-based rate limiting
   - Token bucket algorithm
   - API gateway integration

3. fetch_conversation for top 3 results
   → Reads full implementation discussions

4. search_conversations("Redis rate limiting")
   → Finds 3 more specific results

5. fetch_conversation for 2 additional results
   → Gets implementation details

6. search_conversations("token bucket algorithm")
   → Finds 2 results with algorithm explanation

7. fetch_conversation for 1 more result
   → Confirms understanding

8. Synthesizes comprehensive answer:
   "Based on 6 conversations [IDs listed], here's what we've
   discussed about rate limiting:

   1. Implementation approach: Redis-based with token bucket...
   2. Integration points: API gateway, middleware...
   3. Configuration: Limits per endpoint...
   4. Challenges encountered: Distributed systems...

   [Citations with conversation IDs throughout]"
```

### Scenario: Historical Context

**User:** "How has our thinking evolved on microservices vs monolith?"

**Good LLM behavior:**
```
1. search_conversations("microservices monolith architecture")
2. Sort results by date (from metadata)
3. Fetch conversations chronologically
4. Search for "migration microservices" (discovered concept)
5. Fetch more conversations
6. Create timeline of how thinking evolved
```

## 6. Testing Your Prompts

Try these test questions to see if your prompting works:

**Simple topic:**
```
"What have we discussed about Docker?"
```
Expected: 2-3 searches, 3-5 fetches, comprehensive answer

**Complex topic:**
```
"Research everything about our API strategy"
```
Expected: 4+ searches, 5+ fetches, organized multi-section answer

**Comparative:**
```
"Compare our approaches to authentication across different projects"
```
Expected: Multiple searches for auth + project names, 6+ fetches, comparison matrix

If you're only getting 1 search and 1 fetch, your prompting needs improvement.

## 7. OpenWebUI-Specific Tips

### Custom Model Instructions

In OpenWebUI, you can set per-model instructions:

```
You have access to a conversation archive via MCP tools. When using
these tools, always search multiple times and fetch multiple
conversations. Don't stop after one search - iterate until you have
comprehensive coverage. Treat every archive query as a research task.
```

### Workspace/Chat Instructions

For specific workspaces or chats:

```
This workspace is for researching past technical decisions. Always:
- Search with multiple query variations
- Fetch at least 3 conversations per topic
- Do follow-up searches based on findings
- Cite conversation IDs in every answer
```

## 8. Measuring Effectiveness

Good iteration looks like:

✅ **Multiple tool calls**: 4+ searches, 5+ fetches for complex questions
✅ **Refinement**: Follow-up searches using terms from initial results
✅ **Comprehensive**: Answers synthesize multiple conversations
✅ **Cited**: Conversation IDs included as sources
✅ **Progressive**: Each search builds on previous findings

Poor iteration looks like:

❌ **Single shot**: 1 search, 1 fetch, done
❌ **Surface level**: Only uses snippets, doesn't fetch full content
❌ **Vague**: Answers without specific details or citations
❌ **Repetitive**: Same search multiple times instead of refining

## 9. Troubleshooting

**"LLM only does one search"**
→ Add explicit iteration instructions to system prompt
→ Use research-oriented language in questions
→ Try giving step-by-step research plans

**"LLM doesn't fetch enough conversations"**
→ Tool description says "fetch multiple (2-5)" - emphasize this
→ Ask for comprehensive coverage explicitly
→ Request citations (forces fetching)

**"LLM doesn't do follow-up searches"**
→ Ask "based on what you found, search for..."
→ Request exploration of related concepts
→ Use comparative or analytical questions

**"Results aren't comprehensive"**
→ System prompt should set quality standards
→ Ask for synthesis from multiple sources
→ Request specific number of conversations

## 10. Template System Prompt

Copy-paste ready:

```markdown
# Conversation Archive Research Guidelines

You have access to a conversation archive via MCP tools (search_conversations, fetch_conversation).

## Tool Usage Standards

**search_conversations:**
- Use multiple times with different queries
- Start broad, then refine based on findings
- Try different search_mode values when appropriate
- Review snippets carefully before fetching

**fetch_conversation:**
- Always fetch 2-5 conversations minimum
- Fetch before drawing conclusions
- Use to verify and deepen understanding

## Research Pattern

1. Broad initial search
2. Review results (snippets, scores)
3. Fetch top 3-5 conversations
4. Identify new concepts/terms from content
5. Follow-up searches for specific topics
6. Fetch additional relevant conversations
7. Synthesize comprehensive answer
8. Include conversation IDs as citations

## Quality Checklist

Before answering, ensure you have:
- [ ] Searched at least 2 times
- [ ] Fetched at least 3 conversations
- [ ] Explored related concepts
- [ ] Synthesized from multiple sources
- [ ] Included conversation IDs

Treat every archive query as research, not a keyword lookup.
```

---

## Summary

**Iteration is not automatic** - it requires proper prompting at three levels:

1. **System prompt** - Sets overall research standards
2. **User questions** - Research-oriented language triggers better behavior
3. **Tool descriptions** - Include best practices (already done)

Start with the template system prompt above, then refine based on your specific needs!
