# Testing Patterns

**Analysis Date:** 2025-01-07

## Current Status

**No testing framework configured.** The project has no test files, no test runner configuration, and no testing dependencies. This is documented below along with recommendations for test structure as the codebase grows.

## Test Framework

**Runner:** Not installed

**Recommendation:** Adopt pytest as the standard test runner
- Install: Add `pytest>=7.0` to `pyproject.toml`
- Config file: Create `pyproject.toml` section or `pytest.ini`

**Assertion Library:** 
- Standard Python `assert` statements work with pytest
- No third-party assertion library needed

**Recommended setup in `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

**Run Commands (once installed):**
```bash
pytest                         # Run all tests
pytest -v                      # Verbose output
pytest --watch                 # Watch mode (requires pytest-watch)
pytest --cov                   # Coverage report
pytest tests/                  # Run specific directory
pytest tests/test_main.py      # Run specific file
```

## Test File Organization

**Current structure:**
- No `tests/` directory exists
- No test files present

**Recommended location:**
- Create `tests/` directory at project root (sibling to `main.py`)
- **NOT** co-located with source files

**Recommended structure:**
```
unraid-actuator/
├── main.py
├── pyproject.toml
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── fixtures/          # Reusable test data
├── .python-version
└── README.md
```

## Test Naming Convention

**File naming:**
- `test_*.py` or `*_test.py` (pytest default)
- Example: `test_main.py` for tests of `main.py`

**Test function naming:**
- `test_*` prefix (pytest discovers these automatically)
- Descriptive names: `test_main_prints_welcome_message()` not `test_1()`

**Test class naming (for organization):**
- `Test*` prefix
- Group related tests: `class TestMainFunction:` or `class TestUserAuthentication:`

## Test Structure

**Basic test pattern to adopt:**

```python
# tests/test_main.py
import pytest
from main import main


class TestMain:
    """Tests for main module."""
    
    def test_main_runs_without_error(self, capsys):
        """Verify main() executes successfully."""
        main()
        captured = capsys.readouterr()
        assert captured.out  # Should produce output
    
    def test_main_output_contains_welcome(self, capsys):
        """Verify main prints expected greeting."""
        main()
        captured = capsys.readouterr()
        assert "unraid-actuator" in captured.out
```

**Setup/Teardown patterns:**

```python
# Setup before each test
def setup_method(self):
    """Run before each test method."""
    self.test_data = {"key": "value"}

# Teardown after each test
def teardown_method(self):
    """Run after each test method."""
    self.test_data = None

# Module-level setup/teardown (all tests in file)
def setup_module():
    """Run once before all tests in this module."""
    pass

def teardown_module():
    """Run once after all tests in this module."""
    pass
```

**Using pytest fixtures (recommended over setup/teardown):**

```python
import pytest

@pytest.fixture
def sample_data():
    """Provide test data."""
    return {"id": 1, "name": "test"}

def test_something(sample_data):
    """Test using fixture."""
    assert sample_data["id"] == 1
```

## Mocking

**Framework:** `unittest.mock` (standard library) or `pytest-mock`

**Recommendation:** Use `pytest-mock` for cleaner syntax (optional dependency: `pytest-mock>=3.10`)

**Current test needs:**
- Will likely need to mock external APIs (Unraid interactions)
- May need to mock I/O operations
- Do NOT mock internal functions during unit testing

**Example pattern for adoption:**

```python
from unittest.mock import patch, MagicMock
import pytest

# Using unittest.mock
def test_with_mock():
    with patch('main.external_api_call') as mock_api:
        mock_api.return_value = {"status": "ok"}
        result = main()
        assert mock_api.called

# Using pytest-mock (cleaner)
def test_with_pytest_mock(mocker):
    mock_api = mocker.patch('main.external_api_call')
    mock_api.return_value = {"status": "ok"}
    result = main()
    assert mock_api.called
```

**What to Mock:**
- External API calls (HTTP requests to Unraid API)
- File I/O operations
- System calls
- Database operations (when added)

**What NOT to Mock:**
- Internal functions (test them directly)
- Standard library functions (test with real behavior)
- Business logic (test the actual logic)

## Fixtures and Test Data

**Test Data Location:**
- Small fixtures: Define in `tests/conftest.py` (shared across all tests)
- Test-specific data: Define in individual test files
- Larger datasets: Create `tests/fixtures/` directory

**Example `conftest.py`:**

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_config():
    """Provide standard test configuration."""
    return {
        "api_url": "http://localhost:8080",
        "timeout": 5,
        "retries": 3,
    }

@pytest.fixture
def mock_api_response():
    """Provide mock API response."""
    return {
        "status": "success",
        "data": [{"id": 1, "value": "test"}]
    }
```

**Factory pattern for complex objects:**

```python
class ConfigFactory:
    """Create test configurations."""
    
    @staticmethod
    def basic_config():
        return {"host": "localhost", "port": 8080}
    
    @staticmethod
    def production_config():
        return {"host": "unraid.local", "port": 6789}
```

## Coverage

**Requirements:** Not yet established

**Recommendation:** Target 80%+ coverage; enforce minimum 70% on pull requests

**View Coverage:**
```bash
# Install: pip install pytest-cov

pytest --cov=.              # Coverage for all modules
pytest --cov=main           # Coverage for specific module
pytest --cov --cov-report=html  # HTML report (open htmlcov/index.html)
```

**Configuration in `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
addopts = "--cov=. --cov-report=term-missing"

[tool.coverage.run]
omit = ["tests/*", "*/venv/*"]
```

## Test Types

**Unit Tests:**
- Scope: Individual functions and methods
- Location: `tests/test_*.py`
- Approach: Fast, isolated, no external dependencies
- Current need: Test `main()` function (basic output verification)

**Integration Tests:**
- Scope: Multiple components working together
- Location: `tests/integration/test_*.py` (create when needed)
- Approach: May use test fixtures, temporary files, in-memory databases
- Future need: Test main() + config loading + logging together

**End-to-End Tests:**
- Scope: Full application workflows
- Framework: `pytest` with `requests` library (or similar)
- Location: `tests/e2e/test_*.py` (create when needed)
- Future use: Test actual Unraid API interactions against test instance

**Current testing focus:** Unit tests only (start simple)

## Error Handling Tests

**Pattern for testing exceptions:**

```python
import pytest

def test_invalid_input_raises_error():
    """Verify function raises on invalid input."""
    with pytest.raises(ValueError):
        function_that_should_fail("invalid")

def test_api_error_handled_gracefully(mocker):
    """Verify graceful handling of API failures."""
    mocker.patch('main.api_call', side_effect=ConnectionError)
    result = main()
    assert result is not None  # Should not crash
```

## Async Testing

**Not currently applicable** (main.py has no async code)

**When async is added, use `pytest-asyncio`:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_operation()
    assert result == expected
```

## Current Recommendations

**Immediate next steps:**
1. Add pytest to dev dependencies in `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   dev = ["pytest>=7.0", "pytest-cov>=4.0"]
   ```

2. Create `tests/` directory structure

3. Create `tests/conftest.py` for shared fixtures

4. Write first test file: `tests/test_main.py`

5. Configure pytest in `pyproject.toml` (see section above)

6. Run: `pytest --cov` to verify setup

---

*Testing analysis: 2025-01-07*
*Status: No testing implemented. Patterns and recommendations above provide guidance for establishing testing as project grows.*
