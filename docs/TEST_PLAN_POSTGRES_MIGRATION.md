# PostgreSQL Migration Test Plan - Option A

**Goal**: Ensure comprehensive test coverage for the PostgreSQL implementation to enable safe removal of the legacy ChromaDB backend.

**Strategy**: Test-first, side-by-side verification, then remove legacy.

**Timeline**: 4 weeks

**Coverage Target**: 
- Overall: ≥85%
- Critical paths (search/import/API): ≥95%

---

## Success Criteria (Go/No-Go Gate)

The following criteria must be met before removing legacy ChromaDB:

1. ✅ **API Contract Compliance**: 100% endpoint parity validated
2. ✅ **Search Equivalence**: Deviation ≤5% in top-K overlap
3. ✅ **Data Migration**: 0% data loss, idempotent imports
4. ✅ **Feature Parity**: All features including clipboard functionality pass
5. ✅ **Code Coverage**: PostgreSQL implementation ≥85% overall, ≥95% critical paths
6. ✅ **Integration Tests**: All green with real database and services
7. ✅ **Manual QA**: Sign-off on golden responses and user workflows

---

## Phase 0: Strategy Overview

**Option A (CHOSEN)**: Keep both backends active behind `USE_POSTGRES` flag, build comprehensive parity tests, gate removal on success criteria, then flip default to PostgreSQL and remove legacy in staged PRs.

**Why Option A?**
- De-risks migration with side-by-side validation
- Allows rollback if issues discovered
- Proves PostgreSQL can fully replace ChromaDB before committing
- Provides safety net for one release cycle

---

## Phase 1: Migration Validation Tests (CRITICAL - Week 1)

### Phase 1.0: Test Infrastructure

**File**: `tests/conftest.py` (update), `docker-compose.test.yml` (new)

**Objectives**:
- Isolated PostgreSQL test database (`dovos_test`)
- Fast data seeding and test isolation
- Ability to toggle `USE_POSTGRES` per-test for side-by-side comparison
- Deterministic fake embeddings for speed

**Deliverables**:
```python
# tests/conftest.py additions
@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine with pgvector and pg_trgm"""
    
@pytest.fixture
def db_session(test_db_engine):
    """Provide clean DB session with automatic rollback"""
    
@pytest.fixture
def seed_conversations(db_session):
    """Factory for creating test conversations"""
    
@pytest.fixture
def toggle_postgres_mode(monkeypatch):
    """Toggle USE_POSTGRES flag for comparison tests"""
```

**Test Infrastructure Files**:
- `tests/utils/seed.py` - Data factories (Conversation, Message, Embedding, Job, Settings)
- `tests/utils/fake_embeddings.py` - Deterministic embeddings (seeded RNG, 384-dim vectors)
- `tests/fixtures/chatgpt/` - Sample ChatGPT JSON exports
- `tests/fixtures/claude/` - Sample Claude JSON exports
- `tests/fixtures/large/` - Large datasets (1000+ conversations)
- `tests/fixtures/golden_responses/` - Baseline API responses
- `docker-compose.test.yml` - Test PostgreSQL with pgvector + pg_trgm

**Pytest Markers**:
```ini
# pytest.ini additions
markers =
    migration: Migration validation tests
    unit: Unit tests
    integration: Integration tests
    contract: Contract/golden response tests
    perf: Performance tests (optional)
```

---

### Phase 1.1: API Contract Compliance Tests ⭐⭐⭐ HIGHEST PRIORITY

**File**: `tests/migration/test_api_contract_compliance.py`

**Objective**: Prove all 15+ API endpoints return identical response structures between ChromaDB and PostgreSQL backends.

**Approach**:
1. Seed identical data into both backends
2. Call each endpoint with `USE_POSTGRES=False` and `USE_POSTGRES=True`
3. Assert JSON schemas, field names, types, nesting match exactly
4. Test error scenarios (400, 404, 500) for consistency

**Test Coverage**:

```python
class TestAPIContractCompliance:
    """Validate API contract between legacy and PostgreSQL backends"""
    
    def test_get_conversations_parity(self, both_backends):
        """GET /api/conversations returns identical structure"""
        
    def test_get_conversation_by_id_parity(self, both_backends):
        """GET /api/conversation/<id> returns identical structure"""
        
    def test_search_api_parity(self, both_backends):
        """GET /api/search returns identical structure"""
        
    def test_rag_query_parity(self, both_backends):
        """POST /api/rag/query returns identical structure"""
        
    def test_stats_endpoint_parity(self, both_backends):
        """GET /api/stats returns identical structure"""
        
    def test_collection_count_parity(self, both_backends):
        """GET /api/collection/count returns identical structure"""
        
    def test_error_response_formats(self, both_backends):
        """404/400/500 errors return consistent formats"""
        
    def test_pagination_consistency(self, both_backends):
        """Pagination parameters work identically"""
        
    def test_date_filter_consistency(self, both_backends):
        """Date range filters work identically"""
```

**Endpoints to Cover**:
1. `GET /api/conversations` - List all conversations
2. `GET /api/conversation/<id>` - Get single conversation
3. `GET /api/search` - Simple search (query param)
4. `POST /api/search` - Advanced search with filters
5. `POST /api/rag/query` - RAG query for OpenWebUI
6. `GET /api/rag/health` - Health check
7. `GET /api/stats` - Database statistics
8. `GET /api/collection/count` - Document count
9. `POST /api/export/openwebui/<id>` - Export to OpenWebUI
10. `GET /api/settings` - Get settings
11. `POST /api/settings` - Save settings
12. `DELETE /api/clear` - Clear database
13. `GET /` - Index/conversations list
14. `GET /view/<id>` - View conversation detail
15. `POST /upload` - File upload/import

**Acceptance Criteria**:
- 100% of endpoints return structurally identical responses
- Error messages and status codes match exactly
- Golden responses captured for PostgreSQL baseline

---

### Phase 1.2: Search Equivalence Tests ⭐⭐⭐

**File**: `tests/migration/test_search_equivalence.py`

**Objective**: Prove PostgreSQL search (FTS + pgvector) produces equivalent results to ChromaDB search.

**Approach**:
1. Create curated test corpus with known relevant/irrelevant documents
2. Run same queries on both backends
3. Compare top-K results, rankings, and relevance scores
4. Measure deviation and investigate systematic biases

**Test Coverage**:

```python
class TestSearchEquivalence:
    """Validate search equivalence between backends"""
    
    @pytest.mark.parametrize("query", [
        "python web scraping",
        "database design postgresql",
        "machine learning neural networks",
        "empty query handling",
        "special characters: @#$%",
        "very long query " * 50,
    ])
    def test_fts_search_equivalence(self, both_backends, query):
        """Full-text search produces similar results"""
        # Compare top-10 results
        # Assert overlap >= 80% (8/10 docs match)
        # Compare rank order (Kendall tau correlation)
        
    def test_vector_search_equivalence(self, both_backends):
        """Semantic/vector search produces similar results"""
        # Test cosine similarity distributions
        # Assert top-K overlap >= 85%
        # Allow for small differences due to implementation
        
    def test_hybrid_search_ranking(self, both_backends):
        """Hybrid (FTS + vector) ranking matches"""
        # Test weighted combination
        # Kendall tau correlation >= 0.85
        
    def test_search_with_date_filters(self, both_backends):
        """Date range filters work equivalently"""
        
    def test_search_mode_switching(self, both_backends):
        """Keyword vs semantic mode produces consistent results"""
        
    def test_empty_and_no_results_cases(self, both_backends):
        """Edge cases handle consistently"""
```

**Metrics**:
- **Top-K Overlap**: % of documents appearing in both top-K results
- **Kendall Tau**: Rank correlation between result lists (-1 to 1)
- **Recall@K / Precision@K**: Standard IR metrics
- **Mean Reciprocal Rank (MRR)**: Average 1/rank of first relevant result

**Acceptance Criteria**:
- Top-10 overlap ≥80% for FTS queries
- Top-10 overlap ≥85% for vector queries  
- Overall deviation ≤5% across test suite
- No systematic bias (e.g., PostgreSQL always ranking newer docs higher)

---

### Phase 1.3: Data Migration Tests ⭐⭐⭐

**File**: `tests/migration/test_data_migration.py`

**Objective**: Prove ChatGPT and Claude JSON exports import correctly into PostgreSQL with zero data loss.

**Test Coverage**:

```python
class TestDataMigration:
    """Validate data migration from JSON exports"""
    
    def test_chatgpt_export_import(self, postgres_db):
        """Import ChatGPT JSON preserves all data"""
        # Load fixtures/chatgpt/sample.json
        # Import via postgres_controller.upload()
        # Assert:
        #   - Conversation count matches
        #   - Message count matches
        #   - Timestamps preserved (Unix epoch -> ISO)
        #   - Authors/roles correct
        #   - Message ordering preserved
        #   - Metadata fields intact
        
    def test_claude_export_import(self, postgres_db):
        """Import Claude JSON preserves all data"""
        # Similar assertions for Claude format
        # Timestamps already ISO format
        
    def test_duplicate_detection(self, postgres_db):
        """Re-importing same conversations skips duplicates"""
        # Import once
        # Import again
        # Assert: conversation count unchanged
        # Assert: no duplicate messages
        
    def test_idempotent_reimport(self, postgres_db):
        """Multiple imports of same data are safe"""
        # Import 3 times
        # Verify stable state (no multiplication)
        
    def test_large_dataset_import(self, postgres_db):
        """Import 1000+ conversations efficiently"""
        # Use fixtures/large/
        # Assert: completes within time budget
        # Assert: memory usage reasonable
        # Assert: all data imported correctly
        
    def test_partial_import_recovery(self, postgres_db):
        """Handles errors gracefully without corruption"""
        # Inject failure mid-import
        # Assert: DB in consistent state
        # Assert: retry succeeds
        
    def test_embedding_job_creation(self, postgres_db):
        """Imports enqueue embedding jobs"""
        # After import
        # Assert: jobs created for all messages
        # Assert: job payload correct
```

**Acceptance Criteria**:
- **0% data loss**: All conversations, messages, metadata preserved
- **Idempotent**: Re-running import doesn't duplicate or corrupt
- **Timestamps**: Unix epoch (ChatGPT) and ISO (Claude) correctly handled
- **Embeddings**: Jobs enqueued for all imported messages

---

### Phase 1.4: Feature Parity Tests ⭐⭐⭐

**File**: `tests/migration/test_feature_parity.py`

**Objective**: Prove all features work identically with PostgreSQL backend.

**Test Coverage**:

```python
class TestFeatureParity:
    """Validate feature parity between backends"""
    
    def test_export_to_openwebui(self, both_backends):
        """Export to OpenWebUI produces identical output"""
        
    def test_rag_query_compatibility(self, both_backends):
        """RAG queries work for OpenWebUI integration"""
        # Mock OpenWebUI API calls
        # Verify response format
        
    def test_settings_management(self, both_backends):
        """Settings CRUD operations work"""
        # PostgreSQL has superset of features
        # Ensure non-breaking for clients
        
    def test_file_upload_workflow(self, both_backends):
        """File upload -> parse -> index pipeline works"""
        
    def test_conversation_listing(self, both_backends):
        """Listing/filtering/pagination works"""
        
    def test_stats_and_health_endpoints(self, both_backends):
        """Stats, health, count endpoints work"""
        
    def test_database_clear(self, both_backends):
        """Clear/reset database works safely"""
```

**Copy-to-Clipboard Tests**:

Since clipboard functionality is client-side JavaScript, we have two testing approaches:

**Option 1: UI Tests** (Recommended)

**File**: `tests/ui/test_copy_to_clipboard.py`

```python
# Using Playwright for browser automation
class TestCopyToClipboard:
    """Test copy-to-clipboard functionality"""
    
    def test_copy_conversation_as_markdown(self, browser_page):
        """Copy button converts conversation to markdown"""
        # Navigate to /view/<conversation_id>
        # Click copy button
        # Mock navigator.clipboard.writeText
        # Assert clipboard receives expected markdown:
        #   - Title with # heading
        #   - Date metadata
        #   - Message roles and timestamps
        #   - Content with proper markdown formatting
        
    def test_copy_with_code_blocks(self, browser_page):
        """Code blocks preserved in markdown"""
        # Conversation with code
        # Assert: triple backticks preserved
        
    def test_copy_with_tables(self, browser_page):
        """Tables converted to markdown tables"""
        
    def test_copy_fallback_for_old_browsers(self, browser_page):
        """Fallback method (document.execCommand) works"""
        # Mock navigator.clipboard as undefined
        # Assert: fallback textarea method used
        
    def test_copy_success_message(self, browser_page):
        """Success message displays after copy"""
        # Assert: "Copied!" message appears
        # Assert: message disappears after timeout
        
    def test_copy_error_handling(self, browser_page):
        """Handles clipboard permission errors"""
        # Mock clipboard.writeText rejection
        # Assert: error message displayed
        
    def test_share_search_url(self, browser_page):
        """Share button copies search URL"""
        # On search results page
        # Click share button
        # Assert: URL with query params copied
```

**Setup Required**:
```bash
# Install Playwright
pip install pytest-playwright
playwright install chromium
```

**Option 2: Unit Tests** (If server-side clipboard exists)

**File**: `tests/unit/test_clipboard.py`

Only if you add Python-side clipboard handling (e.g., for API endpoints).

---

## Phase 2: PostgreSQL Core Unit Tests (Week 2)

### Phase 2.1: Repository Comprehensive Tests ⭐⭐

**File**: `tests/unit/test_repositories_comprehensive.py`

Expand existing `tests/unit/test_repositories.py` with exhaustive coverage.

**Test Coverage**:

```python
class TestConversationRepository:
    def test_create_conversation(self, db_session)
    def test_get_by_id(self, db_session)
    def test_get_all_with_pagination(self, db_session)
    def test_get_all_with_sorting(self, db_session)
    def test_update_conversation(self, db_session)
    def test_delete_conversation_cascades_to_messages(self, db_session)
    def test_get_stats(self, db_session)
    def test_search_by_title(self, db_session)
    
class TestMessageRepository:
    def test_create_message(self, db_session)
    def test_get_by_conversation(self, db_session)
    def test_full_text_search(self, db_session)
    def test_trigram_fuzzy_search(self, db_session)
    def test_search_with_special_characters(self, db_session)
    def test_search_with_empty_query(self, db_session)
    def test_message_ordering(self, db_session)
    def test_metadata_json_storage(self, db_session)
    
class TestEmbeddingRepository:
    def test_create_embedding(self, db_session)
    def test_vector_similarity_search(self, db_session)
    def test_cosine_similarity_ordering(self, db_session)
    def test_get_by_message_id(self, db_session)
    def test_update_embedding(self, db_session)
    def test_missing_embeddings_handled(self, db_session)
    def test_get_stats(self, db_session)
    
class TestJobRepository:
    def test_enqueue_job(self, db_session)
    def test_get_pending_jobs(self, db_session)
    def test_update_job_status(self, db_session)
    def test_retry_logic(self, db_session)
    def test_failed_job_handling(self, db_session)
    def test_job_priority_ordering(self, db_session)
    def test_get_queue_stats(self, db_session)
    
class TestSettingRepository:
    def test_create_setting(self, db_session)
    def test_get_setting(self, db_session)
    def test_update_setting(self, db_session)
    def test_delete_setting(self, db_session)
    def test_get_all_settings(self, db_session)
    def test_default_values(self, db_session)

class TestUnitOfWork:
    def test_transaction_commit(self, db_engine)
    def test_transaction_rollback(self, db_engine)
    def test_context_manager(self, db_engine)
    def test_nested_transactions(self, db_engine)
```

**Acceptance Criteria**:
- All repository methods tested
- Edge cases covered (empty, null, special chars, large data)
- Transaction behavior validated

---

### Phase 2.2: Service Unit Tests ⭐⭐

**SearchService Tests**

**File**: `tests/unit/test_search_service.py`

```python
class TestSearchService:
    def test_fts_search_only(self, db_session)
    def test_vector_search_only(self, db_session)
    def test_hybrid_search_ranking(self, db_session)
    def test_search_config_validation(self)
    def test_similarity_threshold_filtering(self, db_session)
    def test_query_expansion(self, db_session)
    def test_result_deduplication(self, db_session)
    def test_empty_query_handling(self, db_session)
    def test_search_with_conversation_filter(self, db_session)
    
    # Property-based tests with Hypothesis
    @given(query=st.text(min_size=1, max_size=500))
    def test_search_never_crashes(self, db_session, query):
        """Search handles any arbitrary input safely"""
```

**MessageService Tests**

**File**: `tests/unit/test_message_service_comprehensive.py`

Expand existing `tests/unit/test_message_service.py`.

```python
class TestMessageService:
    def test_create_with_embedding_job_atomic(self, db_session)
    def test_update_triggers_new_embedding(self, db_session)
    def test_bulk_create_atomic(self, db_session)
    def test_transaction_rollback_on_failure(self, db_session)
    def test_concurrent_creation(self, db_session)
    def test_idempotency(self, db_session)
```

---

### Phase 2.3: Adapter Unit Tests ⭐⭐

**File**: `tests/unit/test_legacy_adapter.py`

**Critical**: The `LegacyAPIAdapter` must be kept even after removing ChromaDB, as it provides the legacy API shape for PostgreSQL.

```python
class TestLegacyAPIAdapter:
    """Test LegacyAPIAdapter provides ChromaDB-compatible API"""
    
    def test_get_all_conversations_format(self, postgres_db):
        """Returns {documents, metadatas, ids} structure"""
        
    def test_conversation_document_formatting(self, postgres_db):
        """Messages formatted with role labels and timestamps"""
        # Assert: "**You said** *(on timestamp)*:"
        # Assert: "**Assistant said** *(on timestamp)*:"
        
    def test_metadata_structure(self, postgres_db):
        """Metadata includes all expected fields"""
        # id, title, source, message_count, timestamps
        
    def test_search_conversations_format(self, postgres_db):
        """Search returns ChromaDB-like structure"""
        
    def test_rag_query_format(self, postgres_db):
        """RAG queries return OpenWebUI-compatible format"""
        
    def test_legacy_id_handling(self, postgres_db):
        """Handles legacy IDs like 'chat-0', 'docx-0'"""
        
    def test_get_stats_format(self, postgres_db):
        """Stats match expected structure"""
```

---

### Phase 2.4: Controller Unit Tests ⭐⭐

**File**: `tests/unit/test_postgres_controller.py`

Mock all repositories/services to isolate controller logic.

```python
class TestPostgresController:
    """Test PostgresController endpoint handlers"""
    
    @pytest.fixture
    def mock_adapter(self, mocker):
        return mocker.Mock(spec=LegacyAPIAdapter)
    
    def test_get_conversations(self, mock_adapter):
        """GET /api/conversations handler"""
        
    def test_api_search_parsing(self, mock_adapter):
        """Parses query params correctly"""
        
    def test_error_handling(self, mock_adapter):
        """Returns proper error responses"""
        
    def test_pagination_params(self, mock_adapter):
        """Handles pagination correctly"""
        
    # Test all 15+ endpoints individually
```

---

## Phase 3: Integration Tests (Week 3)

### Phase 3.1: Embedding Worker Tests ⭐⭐

**File**: `tests/integration/test_embedding_worker_comprehensive.py`

Expand existing `tests/integration/test_embedding_worker.py`.

```python
class TestEmbeddingWorker:
    def test_end_to_end_pipeline(self, postgres_db):
        """Enqueue -> process -> persist -> update status"""
        
    def test_concurrent_workers(self, postgres_db):
        """Multiple workers process jobs safely"""
        
    def test_retry_on_failure(self, postgres_db):
        """Failed jobs retry with backoff"""
        
    def test_graceful_shutdown(self, postgres_db):
        """Workers finish current job before stopping"""
        
    def test_embedding_vector_validation(self, postgres_db):
        """Generated embeddings have correct shape"""
        
    def test_job_saturation_handling(self, postgres_db):
        """Handles large job queue efficiently"""
```

---

### Phase 3.2: Search Integration Tests ⭐⭐

**File**: `tests/integration/test_search_integration.py`

```python
class TestSearchIntegration:
    def test_fts_with_real_data(self, postgres_db):
        """FTS search end-to-end"""
        
    def test_vector_search_with_real_embeddings(self, postgres_db):
        """Vector search with actual embeddings"""
        
    def test_hybrid_search_integration(self, postgres_db):
        """Hybrid search combines both methods"""
        
    def test_search_performance_budget(self, postgres_db):
        """Search completes within time limit"""
        # Assert: P95 latency < 500ms on medium dataset
```

---

### Phase 3.3: Import Workflow Tests ⭐⭐

**File**: `tests/integration/test_import_workflows.py`

```python
class TestImportWorkflows:
    def test_complete_import_workflow(self, postgres_db):
        """Upload -> parse -> insert -> embeddings"""
        
    def test_duplicate_handling(self, postgres_db):
        """Idempotent imports"""
        
    def test_error_recovery(self, postgres_db):
        """Graceful handling of malformed JSON"""
```

---

### Phase 3.4: API Integration Tests ⭐⭐

**File**: `tests/integration/test_postgres_api_comprehensive.py`

Expand existing `tests/integration/test_postgres_api_compatibility.py`.

Test all endpoints with real database and services running.

---

## Phase 4: Database & Schema Tests (Week 3)

### Phase 4.1: Database Schema Validation

**File**: `tests/unit/test_database_schema.py`

```python
class TestDatabaseSchema:
    def test_conversation_model(self, db_session):
        """Conversation model defined correctly"""
        
    def test_message_model_constraints(self, db_session):
        """Message role constraint works"""
        
    def test_relationships(self, db_session):
        """Cascade deletes work"""
        
    def test_indexes_exist(self, db_session):
        """Required indexes created"""
        # GIN, pgvector, pg_trgm indexes
        
    def test_extensions_loaded(self, db_session):
        """pgvector and pg_trgm extensions active"""
        
    def test_generated_columns(self, db_session):
        """tsvector column auto-updates"""
```

---

### Phase 4.2: Alembic Migration Tests

**File**: `tests/integration/test_alembic_migrations.py`

```python
class TestAlembicMigrations:
    def test_upgrade_from_empty(self):
        """Can create schema from scratch"""
        
    def test_downgrade_and_upgrade(self):
        """Can rollback and re-apply migrations"""
        
    def test_data_preservation(self):
        """Data survives migrations"""
```

---

## Phase 5: Contract & Regression Tests (Week 3)

### Phase 5.1: Golden Responses

**File**: `tests/contract/test_golden_responses.py`

```python
class TestGoldenResponses:
    """Compare current output to golden baselines"""
    
    def test_api_responses_match_golden(self, postgres_db):
        """Responses match saved golden files"""
        # Load tests/fixtures/golden_responses/*.json
        # Compare structure and sample values
```

---

## Phase 6: Performance Tests (Week 4)

**File**: `tests/perf/test_performance.py`

```python
@pytest.mark.perf
class TestPerformance:
    def test_large_import_performance(self):
        """Import 100k+ messages within budget"""
        
    def test_search_latency(self):
        """Search P95 < 500ms"""
        
    def test_worker_throughput(self):
        """Embeddings generated at target rate"""
```

---

## Phase 7: CI Pipeline (Week 4)

**Setup**:
- GitHub Actions or similar CI
- Matrix: `{backend: [legacy, postgres]}` for migration tests
- Parallel execution for unit tests
- Docker Compose for integration tests

**Coverage Gates**:
- PostgreSQL code coverage ≥85%
- Critical paths (search/import/API) ≥95%
- All migration tests pass
- Search deviation ≤5%

**Artifacts**:
- Coverage reports (HTML, XML)
- Golden snapshot diffs
- Test logs

---

## Phase 8: Pre-Removal Readiness (Week 4)

**Checklist**:
- [ ] All tests passing
- [ ] Coverage thresholds met
- [ ] Search equivalence validated (≤5% deviation)
- [ ] Data migration 0% loss
- [ ] Feature parity including clipboard
- [ ] Manual QA sign-off
- [ ] Golden responses approved
- [ ] Release notes prepared
- [ ] Migration runbook ready

---

## Phase 9: Removal Plan (Option A)

### PR 1: Flip Default (Release 1)
- Change `USE_POSTGRES` default to `True` in `config.py`
- Keep legacy code behind flag
- Add deprecation warning when legacy mode used
- Update documentation
- Monitor for issues

### PR 2: Code Removal (Release 2 - after monitoring period)
**Remove**:
- `models/conversation_model.py`
- `rag_service.py`
- `models/fts_model.py`
- `models/search_model.py`
- Feature flag logic in `routes.py` and `app.py`
- `chromadb` from `requirements.txt`
- ChromaDB-specific configs

**Keep**:
- `db/adapters/legacy_api_adapter.py` (provides legacy API shape for PostgreSQL)

### PR 3: Cleanup
- Run Alembic sanity checks
- Remove unused legacy DB tables/indexes
- Update all documentation
- Archive legacy test files

**Rollback Plan**:
- Tag last dual-backend release (`v1.x-dual-backend`)
- Keep emergency patch branch ready
- Can temporarily re-enable legacy flag if critical issues

---

## Phase 10: Post-Removal Validation

**Monitoring**:
- Error rates
- Search quality metrics
- Import success rates
- Worker throughput

**Health Checks**:
- Add runtime health endpoints
- Monitor PostgreSQL performance
- Track embedding queue depth

**Follow-up**:
- Prune legacy golden responses after one release
- Remove legacy test fixtures

---

## File Deliverables Summary

### New Test Files

**Migration Tests** (tests/migration/):
- `test_api_contract_compliance.py` - API parity validation
- `test_data_migration.py` - Import correctness
- `test_search_equivalence.py` - Search comparison
- `test_feature_parity.py` - Feature compatibility

**Unit Tests** (tests/unit/):
- `test_repositories_comprehensive.py` - All repositories
- `test_search_service.py` - Search ranking
- `test_message_service_comprehensive.py` - Message service
- `test_legacy_adapter.py` - API adapter
- `test_postgres_controller.py` - Controller handlers
- `test_database_schema.py` - Schema validation
- `test_clipboard.py` - Clipboard (if server-side)

**Integration Tests** (tests/integration/):
- `test_embedding_worker_comprehensive.py` - Worker pipeline
- `test_search_integration.py` - Search E2E
- `test_import_workflows.py` - Import E2E
- `test_postgres_api_comprehensive.py` - API E2E
- `test_alembic_migrations.py` - Migration safety

**Contract Tests** (tests/contract/):
- `test_golden_responses.py` - Golden baselines
- `test_regression.py` - Regression detection

**UI Tests** (tests/ui/):
- `test_copy_to_clipboard.py` - Clipboard functionality (Playwright)

**Performance Tests** (tests/perf/):
- `test_performance.py` - Performance benchmarks

### Test Utilities

**Fixtures** (tests/fixtures/):
- `chatgpt/` - Sample ChatGPT exports
- `claude/` - Sample Claude exports
- `large/` - Large datasets
- `golden_responses/` - API baselines

**Utilities** (tests/utils/):
- `seed.py` - Data factories
- `fake_embeddings.py` - Deterministic embeddings

### Infrastructure

- `docker-compose.test.yml` - Test database setup
- Update `tests/conftest.py` - Fixtures and setup
- Update `pytest.ini` - Markers and config

---

## Timeline: 4-Week Schedule

### Week 1: Migration Validation (Critical)
- **Day 1-2**: Phase 1.0 (infrastructure)
- **Day 3-4**: Phase 1.1 (API contract tests)
- **Day 5**: Phase 1.2 (search equivalence)

### Week 2: Core Unit Tests
- **Day 1-2**: Phase 1.3 (data migration)
- **Day 3**: Phase 1.4 (feature parity + clipboard)
- **Day 4-5**: Phase 2.1-2.2 (repositories, services)

### Week 3: Integration & Schema
- **Day 1-2**: Phase 2.3-2.4 (adapter, controller)
- **Day 3**: Phase 3.1-3.2 (workers, search integration)
- **Day 4**: Phase 3.3-3.4 (import, API integration)
- **Day 5**: Phase 4.1-4.2, 5.1 (schema, migrations, contracts)

### Week 4: Performance, CI, Removal
- **Day 1**: Phase 6 (performance tests)
- **Day 2**: Phase 7 (CI pipeline setup)
- **Day 3**: Phase 8 (readiness review)
- **Day 4**: Phase 9 (removal PRs)
- **Day 5**: Phase 10 (post-removal validation)

---

## Success Metrics

**Quantitative**:
- ✅ Coverage: ≥85% overall, ≥95% critical paths
- ✅ Search deviation: ≤5% top-K overlap
- ✅ Data migration: 0% loss
- ✅ Test suite: <5 minutes for unit, <15 minutes total
- ✅ API compatibility: 100% endpoints identical

**Qualitative**:
- ✅ Manual QA approval
- ✅ Documentation complete
- ✅ Team confidence in migration
- ✅ Rollback plan validated

---

## Risk Mitigation

**Risks**:
1. **Search quality degradation** → Mitigation: Extensive equivalence testing, monitoring
2. **Data loss during migration** → Mitigation: 0% loss acceptance criteria, backup plan
3. **Performance regression** → Mitigation: Performance tests, load testing
4. **API breaking changes** → Mitigation: Contract tests, golden responses
5. **Embedding worker failures** → Mitigation: Retry logic, dead-letter queue tests

**Rollback Strategy**:
- Dual-backend mode for one release
- Tagged fallback release
- Emergency patch branch ready

---

## Next Steps

1. **Review and approve this plan**
2. **Set up test infrastructure** (Phase 1.0)
3. **Begin Phase 1.1** (API contract tests) - highest priority
4. **Iterate through phases** following timeline
5. **Gate removal on success criteria** (Phase 8)
6. **Execute removal plan** (Phase 9)
7. **Monitor post-removal** (Phase 10)

---

## Questions & Clarifications

Before proceeding, confirm:
- ✅ Coverage targets acceptable (85% overall, 95% critical)?
- ✅ Timeline realistic (4 weeks)?
- ✅ Playwright acceptable for clipboard tests?
- ✅ Success criteria complete?
- ✅ Removal strategy (Option A) approved?

---

**Document Version**: 1.0  
**Date**: 2025-10-22  
**Status**: Ready for Review
