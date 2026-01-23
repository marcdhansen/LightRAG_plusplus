# LightRAG Testing Framework

This project uses `pytest` for both automated and manual testing.

## Test Markers

We use the following markers to categorize tests:

- `@pytest.mark.light`: Fast tests (unit tests, mocks, pure logic) that run in seconds. Run with `pytest -m light` or `./scripts/test_light.sh`.
- `@pytest.mark.heavy`: Slow tests (integration, external interactions, stress tests). Run with `pytest -m heavy` or `./scripts/test_heavy.sh`.
- `@pytest.mark.offline`: Tests that don't require any external services (DB, API, LLM). Run these with `pytest -m offline`.
- `@pytest.mark.integration`: Tests that require external services (Memgraph, Ollama, etc.). These are **skipped by default**.
- `@pytest.mark.requires_api`: Sub-category of integration tests that specifically require the LightRAG API server to be running.
- `@pytest.mark.manual`: Tests intended for manual execution or observation. These are **skipped by default**.

## Running Tests

### 1. Light Tests (Recommended for CI/local dev)
Run fast tests that cover core logic without external dependencies delays.
```bash
./scripts/test_light.sh
# OR
pytest -m light
```

### 2. Heavy Tests (Integration/Full System)
Run comprehensive tests involving databases, LLMs, and API servers.
```bash
./scripts/test_heavy.sh
# OR
pytest -m heavy
```

### 3. Simple Offline Tests (Fast)
```bash
pytest -m offline
```

### 4. Integration Tests (Legacy Flag)
To run tests that require external services, use the `--run-integration` flag:
```bash
pytest --run-integration
```

### 5. Manual Tests
To run tests designated for manual verification:
```bash
pytest --run-manual
```

### 6. Combining Flags
You can run everything with:
```bash
pytest --run-integration --run-manual
```

## Creating Manual Tests

Manual tests should be marked with `@pytest.mark.manual`. They can include `input()` prompts if human interaction is needed, or simply perform checks that are better suited for manual observation.

```python
import pytest

@pytest.mark.manual
def test_manual_verification():
    print("\nPlease verify that the WebUI shows the correct graph.")
    # You can even use input() if running with -s
    # response = input("Does it look correct? (y/n): ")
    # assert response.lower() == 'y'
    assert True
```

**Note**: To see output and interact with `input()`, always run pytest with the `-s` flag:
```bash
pytest --run-manual -s
```
