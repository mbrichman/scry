# Handling Sensitive Data in Test Golden Responses

## Problem
Golden response files in `tests/golden_responses/` now contain:
- Real conversation content (personal user data)
- User messages with private information
- Potentially identifying metadata
- Real database statistics and models

These files are committed to git and could expose sensitive information if the repository becomes public or is shared.

## Scope
- 7 JSON files in `tests/golden_responses/`
- Files contain actual chat conversations from the database
- Used for API contract validation and regression testing

## Recommended Solutions

### Option 1: Synthetic Data Generation (Recommended)
Create a fixture that generates realistic but synthetic data:
- **Pros**: 
  - No sensitive data leaked
  - Deterministic/reproducible
  - Can be version controlled safely
  - Tests still validate contract and structure
- **Cons**: 
  - More complex setup
  - Less realistic edge cases

**Implementation**:
1. Create `tests/fixtures/synthetic_responses.py` with generators
2. Generate responses with fake but realistic data:
   - Synthetic conversation IDs (UUIDs)
   - Generic but realistic conversation titles
   - Realistic message structures without personal content
   - Generic query results without real conversation data
3. Replace golden responses with synthetic data

### Option 2: Data Sanitization
Automatically strip sensitive fields from real responses:
- **Pros**:
  - Can capture real structure/edge cases
  - Can use real data initially
- **Cons**:
  - Risk of missing sensitive fields
  - Harder to maintain list of sensitive fields
  - Binary content, attachments harder to sanitize

**Implementation**:
1. Create `tests/utils/response_sanitizer.py` with sanitization rules
2. Define what constitutes sensitive: full content, metadata, IDs, etc.
3. Run sanitizer before saving golden responses
4. Audit manually for missed sensitive data

### Option 3: Exclude from Version Control
Store golden responses outside git:
- **Pros**:
  - Simple to implement
- **Cons**:
  - Must be regenerated on each fresh clone
  - CI/CD complications
  - Tests may fail on fresh checkout
  - Not truly version controlled

**Implementation**:
1. Add `tests/golden_responses/*.json` to `.gitignore`
2. Create generation script that runs in CI
3. Tests skip if responses missing locally

### Option 4: Anonymized Fixtures
Create intermediate fixture layer that converts real data:
- **Pros**:
  - Can use real API responses for structure validation
  - Can anonymize before storage
- **Cons**:
  - Performance overhead
  - Complex mapping layer

## Recommended Approach: Option 1 + Option 2

### Phase 1: Immediate (Today)
- Create `tests/fixtures/synthetic_responses.py` with response generators
- Generate realistic but safe responses for each endpoint
- Update tests to use synthetic data as primary source
- Remove current golden response files from git tracking

### Phase 2: Testing Strategy
- Keep live integration tests (they run with real DB, don't commit responses)
- Use synthetic responses for contract/regression validation
- Document live test process (for manual testing with real data)

### Phase 3: Documentation
- Document what each synthetic response represents
- Add comments explaining why fields are synthetic
- Create guide for regenerating if needed

## Files to Create
1. `tests/fixtures/synthetic_responses.py` - Response generators
2. `.gitignore` update - Exclude golden responses
3. `tests/integration/test_live_api_regeneration.py` - How to regenerate responses with real DB
4. Update existing tests to use synthetic responses

## Migration Path
1. Create synthetic response generators
2. Update conftest to provide synthetic responses
3. Verify all tests pass with synthetic data
4. Remove sensitive golden response files from git
5. Add to .gitignore

## Example Synthetic Response Structure
```python
def generate_conversations_response():
    """Generate a realistic but synthetic GET /api/conversations response"""
    return {
        "documents": [
            "How can I improve my productivity?",
            "What are the best practices for testing?",
            "Tell me about machine learning"
        ],
        "ids": [str(uuid4()) for _ in range(3)],
        "metadatas": [
            {"source": "chatgpt", "date": "2024-01-15"},
            {"source": "claude", "date": "2024-01-14"},
            {"source": "openwebui", "date": "2024-01-13"}
        ]
    }
```

## Action Items
- [ ] Create synthetic response generators
- [ ] Update tests to use synthetic responses
- [ ] Verify all tests pass with synthetic data
- [ ] Remove sensitive golden responses from git
- [ ] Add golden_responses to .gitignore
- [ ] Document the process
- [ ] Update CI/CD if needed
