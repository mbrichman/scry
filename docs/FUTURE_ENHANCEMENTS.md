# Future Enhancements for Dovos

**Last Updated:** December 2025  
**Current Status:** 531 tests passing, 60% code coverage, clean service architecture  
**Major Refactoring:** Completed (see `docs/SERVICE_LAYER_ARCHITECTURE.md`)

---

## Current State

### Test Suite Health
- ✅ **531 passing** (99.8%)
- ✅ **1 skipped** (documented, legitimate)
- ✅ **60% code coverage** overall
- ✅ **88-100% service coverage** (4 services)
- ✅ **Clean SOLID architecture**

### Recent Improvements
- ✅ Controller refactored (1171 → 473 lines, 60% reduction)
- ✅ 4 services created with comprehensive tests
- ✅ All legacy code removed
- ✅ Proper logging throughout
- ✅ Zero regressions

---

## Potential Enhancements

### Enhancement 1: Additional Route Integration Tests
**Priority:** Medium  
**Effort:** 1 week  
**Current Coverage:** Partial (~15% of routes)

#### Untested Routes
- `POST /upload` - File upload handling
- `POST /export_to_openwebui/<doc_id>` - Export functionality  
- `DELETE /api/conversation/<doc_id>` - Delete conversation
- `POST /clear_db` - Clear database
- `GET /settings` - Settings retrieval
- `POST /api/settings` - Settings update

#### Approach
Create `tests/integration/test_routes_complete.py` with:

```python
def test_upload_docx_file(client):
    """Test uploading DOCX file via HTTP."""
    # Create test file
    # POST to /upload
    # Verify conversation created
    # Verify messages extracted

def test_delete_conversation(client, seed_conversations):
    """Test DELETE endpoint."""
    conv, _ = seed_conversations(count=1)[0]
    
    response = client.delete(f'/api/conversation/{conv.id}')
    
    assert response.status_code == 200
    assert response.json['success'] == True
    
    # Verify conversation deleted
    response = client.get(f'/api/conversation/{conv.id}')
    assert response.status_code == 404

def test_settings_management(client):
    """Test settings GET/POST endpoints."""
    response = client.get('/settings')
    assert response.status_code == 200
    
    response = client.post('/api/settings', json={
        'openwebui_url': 'http://test.example.com'
    })
    assert response.status_code == 200
```

#### Error Case Tests
```python
def test_invalid_conversation_id_404(client):
    """Test 404 for invalid conversation ID."""
    response = client.get('/api/conversation/invalid-uuid')
    assert response.status_code == 404

def test_malformed_json_400(client):
    """Test 400 for malformed request data."""
    response = client.post('/api/rag/query', data='not-json')
    assert response.status_code == 400
```

#### Success Criteria
- ✅ All untested routes have tests
- ✅ Error handling validated (404, 400, 500)
- ✅ File upload tested
- ✅ Settings management tested

---

### Enhancement 2: End-to-End Workflow Tests
**Priority:** Medium  
**Effort:** 1 week

#### Test Workflows

**1. Upload → Search → View → Export**
```python
def test_complete_conversation_workflow(client):
    """Test full conversation lifecycle."""
    # Upload DOCX file
    # Wait for embeddings
    # Search for content
    # Verify results
    # Export to markdown
    # Export to OpenWebUI
```

**2. Bulk Upload → RAG Query**
```python
def test_multi_conversation_rag(client):
    """Test RAG across multiple conversations."""
    # Upload multiple conversations
    # Perform RAG queries
    # Verify contextual results
    # Test deduplication
```

**3. Settings Management Workflow**
```python
def test_settings_persistence(client):
    """Test settings across app restarts."""
    # Configure OpenWebUI URL
    # Test export with settings
    # Verify settings persistence
```

**4. Conversation Lifecycle**
```python
def test_conversation_crud_lifecycle(client):
    """Test create, read, update, delete cycle."""
    # Create conversation
    # Add messages
    # Search conversation
    # Update conversation
    # Delete conversation
    # Verify cleanup
```

#### New Test Files
- `tests/e2e/test_complete_workflows.py`
- `tests/e2e/test_upload_to_export.py`
- `tests/e2e/test_settings_workflow.py`

#### Success Criteria
- ✅ 4+ complete workflows tested
- ✅ End-to-end validation of critical paths
- ✅ Integration with external services (OpenWebUI) tested
- ✅ Error recovery tested

---

### Enhancement 3: Performance Benchmarks
**Priority:** Low  
**Effort:** 3-5 days

#### Scenarios to Benchmark

**1. Search Performance**
```python
def test_search_performance_10k_conversations(benchmark, seed_conversations):
    """Benchmark search with 10k conversations."""
    seed_conversations(count=10000, with_embeddings=True)
    
    def search():
        return search_service.search("test query", limit=10)
    
    result = benchmark(search)
    assert result.stats.mean < 0.5  # Should complete in < 500ms
```

**2. RAG Query Latency**
```python
def test_rag_query_latency(benchmark):
    """Benchmark RAG query response time."""
    def rag_query():
        return contextual_service.retrieve_with_context(
            query="test query",
            top_k_windows=5
        )
    
    result = benchmark(rag_query)
    assert result.stats.mean < 1.0  # Should complete in < 1s
```

**3. Concurrent API Requests**
```python
def test_concurrent_search_requests(client):
    """Test API under concurrent load."""
    import concurrent.futures
    
    def make_request():
        return client.get('/api/search?q=test')
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in futures]
    
    assert all(r.status_code == 200 for r in results)
```

**4. Large Conversation Imports**
```python
def test_import_large_conversation(benchmark):
    """Benchmark importing conversation with 1000+ messages."""
    large_doc = create_conversation_with_messages(1000)
    
    result = benchmark(lambda: import_service.import_conversation(large_doc))
    assert result.stats.mean < 5.0  # Should complete in < 5s
```

**5. Embedding Generation Throughput**
```python
def test_embedding_generation_throughput(benchmark):
    """Benchmark embedding generation rate."""
    messages = [f"Test message {i}" for i in range(100)]
    
    result = benchmark(lambda: embedding_service.generate_embeddings(messages))
    throughput = 100 / result.stats.mean
    assert throughput > 20  # Should process >20 messages/sec
```

#### Tools
- `pytest-benchmark` - For benchmark tests
- `locust` - For load testing (separate tool)

#### New Directory
Create: `tests/perf/`

#### Success Criteria
- ✅ Baseline metrics established
- ✅ Performance regression tests in place
- ✅ Load testing scenarios defined
- ✅ Performance bottlenecks identified

---

### Enhancement 4: Additional Service Tests
**Priority:** Low  
**Effort:** 1 week

#### Services to Add
- **ValidationService**: Input validation logic
- **AuthorizationService**: When auth is added
- **CacheService**: For performance optimization
- **NotificationService**: For user notifications

#### Existing Services to Enhance
- Add more edge case tests to existing services
- Test error recovery paths
- Test concurrent access scenarios

---

### Enhancement 5: Security Testing
**Priority:** Medium (when deploying to production)  
**Effort:** 1 week

#### Security Test Categories

**1. Input Validation**
```python
def test_sql_injection_prevention(client):
    """Test SQL injection protection."""
    malicious_input = "'; DROP TABLE conversations; --"
    response = client.get(f'/api/search?q={malicious_input}')
    assert response.status_code in [200, 400]
    # Verify database intact

def test_xss_prevention(client, seed_conversations):
    """Test XSS protection in conversation content."""
    xss_content = "<script>alert('xss')</script>"
    # Create conversation with XSS content
    # Verify content is escaped in response
```

**2. Authentication/Authorization** (when implemented)
```python
def test_unauthorized_access_401(client):
    """Test unauthorized access returns 401."""
    response = client.get('/api/conversations')  # Without auth token
    assert response.status_code == 401

def test_invalid_token_403(client):
    """Test invalid token returns 403."""
    response = client.get('/api/conversations', 
                         headers={'Authorization': 'Bearer invalid'})
    assert response.status_code == 403
```

**3. Rate Limiting** (when implemented)
```python
def test_rate_limiting(client):
    """Test rate limiting on API endpoints."""
    for i in range(100):
        response = client.get('/api/search?q=test')
        if i < 50:
            assert response.status_code == 200
        else:
            assert response.status_code == 429  # Too many requests
```

#### Success Criteria
- ✅ Input validation tested
- ✅ SQL injection prevention verified
- ✅ XSS prevention verified
- ✅ Authentication/authorization tested (when implemented)
- ✅ Rate limiting tested (when implemented)

---

## Known Technical Debt

### Issue: Intermittent Torch Model Loading
**Tests affected:**
- `test_hybrid_search_returns_results`
- `test_search_basic_functionality_summary`

**Problem:** Race condition in torch model initialization on Apple Silicon  
**Impact:** ~98% pass rate in full suite, pass when run individually  
**Workaround:** Tests are valid, issue is environmental  
**Permanent fix:** Requires torch/sentence-transformers update or model pre-loading

### Issue: Skipped Integration Test
**Test:** `test_retrieve_with_context_integration`  
**Reason:** Requires full embeddings setup with background workers  
**Status:** Legitimate skip, not a bug

---

## Testing Commands Reference

### Run Full Suite
```bash
source venv/bin/activate
pytest tests/ --tb=no -q
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
open htmlcov/index.html
```

### Run Specific Categories
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only (when implemented)
pytest tests/e2e/ -v

# Service tests only
pytest tests/unit/services/ -v
```

### Run Performance Tests (when implemented)
```bash
pytest tests/perf/ --benchmark-only
```

### Run with Test Marks
```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

---

## Getting Started on Enhancements

### General Approach
1. Create a new branch: `git checkout -b add-<enhancement-name>`
2. Create test file(s) in appropriate directory
3. Start with simple happy path tests
4. Add error case tests
5. Run coverage to measure progress
6. Iterate until success criteria met
7. Commit and create PR

### For Route Tests
1. Use Flask test client from conftest
2. Test one route at a time
3. Verify request/response formats match API contracts
4. Test error codes (404, 400, 500)
5. Use existing fixtures from conftest.py

### For E2E Tests
1. Use full application context
2. Seed real test data
3. Test complete workflows, not individual operations
4. Clean up test data after each test
5. Use transaction rollback where possible

### For Performance Tests
1. Install pytest-benchmark: `pip install pytest-benchmark`
2. Use realistic data volumes
3. Establish baseline metrics first
4. Set reasonable thresholds based on baselines
5. Run on consistent hardware for comparison

---

## Resources

### Documentation
- `docs/SERVICE_LAYER_ARCHITECTURE.md` - Service layer design
- `docs/` - Additional architecture documentation
- `README.md` - Project overview

### Code References
- `tests/conftest.py` - Fixture definitions and patterns
- `tests/integration/test_api_conversations.py` - Good integration test examples
- `tests/unit/test_contextual_retrieval.py` - Good unit test examples
- `tests/unit/services/` - Service test examples

### External Resources
- [pytest documentation](https://docs.pytest.org/)
- [Flask testing](https://flask.palletsprojects.com/en/latest/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [Locust (load testing)](https://locust.io/)

---

## Priority Recommendations

### Short Term (1-2 months)
1. **Enhancement 1**: Route integration tests
   - Fills coverage gaps in critical paths
   - Low risk, high value

### Medium Term (3-6 months)
2. **Enhancement 2**: E2E workflow tests
   - Validates complete user journeys
   - Catches integration issues

3. **Enhancement 5**: Security testing
   - Important before production deployment
   - Identifies vulnerabilities early

### Long Term (6-12 months)
4. **Enhancement 3**: Performance benchmarks
   - Establishes baseline metrics
   - Prevents performance regressions

5. **Enhancement 4**: Additional services
   - As features are added
   - Maintains clean architecture

---

**Note:** All enhancements are optional improvements to an already healthy test suite. The current state (531 passing tests, 60% coverage) is production-ready for most use cases.
