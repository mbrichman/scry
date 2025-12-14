# Migration Test Runner Framework

Structured test execution and reporting framework for the PostgreSQL migration validation suite.

## Overview

The test runner provides:
- Phase-based test execution
- Comprehensive reporting with JSON output
- Success criteria validation (≥95% pass rate per phase)
- Stop-on-failure support
- Coverage integration
- Human-readable summaries

## Quick Start

### Run Quick Validation (Infrastructure + Contract)
```bash
python -m tests.utils.test_runner quick
```

### Run Full Migration Suite
```bash
python -m tests.utils.test_runner full
```

### Programmatic Usage
```python
from tests.utils.test_runner import MigrationTestRunner, TestPhase

runner = MigrationTestRunner(output_dir=Path("test_reports"))

# Run specific phase
report = runner.run_phase(TestPhase.PHASE_1_1, test_markers=["migration", "contract"])

# Run multiple phases
report = runner.run_migration_suite(
    phases=[TestPhase.PHASE_1_0, TestPhase.PHASE_1_1],
    stop_on_failure=True
)

# Check results
if report.all_phases_passing:
    print("✓ All phases passed")
else:
    print("✗ Some phases failed")
```

## Test Phases

| Phase | Name | Markers | Description |
|-------|------|---------|-------------|
| 1.0 | Infrastructure | `migration`, `infrastructure` | Database setup, fixtures, seeding |
| 1.1 | Contract Compliance | `migration`, `contract` | API response validation |
| 1.2 | Search Equivalence | `migration`, `search` | Search result parity |
| 1.3 | Data Migration | `migration`, `data` | Zero data loss validation |
| 1.4 | Feature Parity | `migration`, `feature` | Clipboard and other features |
| 2.0 | Integration | `integration` | End-to-end workflows |
| 3.0 | Performance | `perf` | Response time and throughput |
| 4.0 | Edge Cases | `migration`, `edge` | Error handling and limits |
| 5.0 | Load Testing | `perf`, `load` | Concurrent user simulation |

## Reports

### JSON Report Structure
```json
{
  "start_time": "2025-01-15T10:30:00",
  "end_time": "2025-01-15T10:35:00",
  "total_duration": 300.5,
  "overall_success_rate": 98.5,
  "all_phases_passing": true,
  "summary": {
    "passed": 45,
    "failed": 1,
    "skipped": 2,
    "errors": 0
  },
  "phases": [
    {
      "phase": "1.0_infrastructure",
      "total_tests": 10,
      "passed": 10,
      "failed": 0,
      "skipped": 0,
      "errors": 0,
      "duration": 5.2,
      "success_rate": 100.0,
      "is_passing": true,
      "coverage_pct": 85.5
    }
  ]
}
```

### Console Output
```
================================================================================
MIGRATION TEST REPORT
================================================================================
Start Time: 2025-01-15T10:30:00
End Time: 2025-01-15T10:35:00
Total Duration: 300.50s

Overall Success Rate: 98.5%
All Phases Passing: ✓ YES

Overall Summary:
  Passed:  45
  Failed:  1
  Skipped: 2
  Errors:  0

Phase Results:

  ✓ 1.0_infrastructure
    Tests: 10/10 passed (100.0%)
    Duration: 5.20s
    Coverage: 85.5%

  ✓ 1.1_contract_compliance
    Tests: 15/15 passed (100.0%)
    Duration: 12.35s

================================================================================
```

## Success Criteria

Each phase must meet:
- ≥95% test pass rate
- Zero errors
- All critical paths validated

The migration cannot proceed to production until `all_phases_passing == true`.

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Migration Tests
  run: python -m tests.utils.test_runner full

- name: Upload Test Reports
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: migration-test-reports
    path: test_reports/
```

### Pre-commit Hook
```bash
#!/bin/bash
python -m tests.utils.test_runner quick
if [ $? -ne 0 ]; then
    echo "❌ Migration tests failed"
    exit 1
fi
```

## Dependencies

Requires `pytest-json-report` for JSON output:
```bash
pip install pytest-json-report
```

Add to `pytest.ini`:
```ini
[pytest]
markers =
    migration: PostgreSQL migration tests
    infrastructure: Database and fixture tests
    contract: API contract compliance tests
    search: Search equivalence tests
    data: Data migration tests
    feature: Feature parity tests
    integration: Integration tests
    perf: Performance tests
    edge: Edge case tests
    load: Load testing
```

## Advanced Usage

### Custom Phase Selection
```python
from tests.utils.test_runner import MigrationTestRunner, TestPhase

runner = MigrationTestRunner()
report = runner.run_migration_suite(
    phases=[
        TestPhase.PHASE_1_1,
        TestPhase.PHASE_1_2,
        TestPhase.PHASE_1_3
    ],
    stop_on_failure=False  # Continue even if a phase fails
)
```

### Custom Pytest Arguments
```python
phase_report = runner.run_phase(
    TestPhase.PHASE_1_1,
    test_markers=["migration", "contract"],
    pytest_args=[
        "-x",  # Stop on first failure
        "--tb=short",  # Short traceback format
        "-k", "test_search"  # Only run tests matching pattern
    ]
)
```

### Parsing Reports Programmatically
```python
import json
from pathlib import Path

# Load latest report
reports_dir = Path("test_reports")
latest_report = max(reports_dir.glob("migration_report_*.json"))

with open(latest_report) as f:
    data = json.load(f)

# Check specific phase
contract_phase = next(
    p for p in data["phases"] 
    if p["phase"] == "1.1_contract_compliance"
)

if not contract_phase["is_passing"]:
    print(f"Contract compliance failed: {contract_phase['failed']} tests")
```

## Troubleshooting

### JSON Report Not Generated
Ensure `pytest-json-report` is installed:
```bash
pip install pytest-json-report
```

### Phase Always Failing
Check marker configuration in `pytest.ini` and ensure tests are properly decorated:
```python
import pytest

@pytest.mark.migration
@pytest.mark.contract
def test_api_contract():
    ...
```

### Stop-on-Failure Not Working
Verify the phase is actually failing (not skipped) and `stop_on_failure=True` is set.
