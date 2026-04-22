<!-- GSD:project-start source:PROJECT.md -->
## Project

**unraid-actuator**

`unraid-actuator` is a `uv`-buildable Python package and CLI for Unraid that reconciles a host's running Docker Compose configuration against a Git-managed infrastructure repository. It is built for homelab operators managing several servers separately, with each actuator instance owning one host's view of apps, environments, secrets, validation, build artifacts, and deployment actions.

The tool turns a repository organized as `[host]/[app]/[environment]/...` into a safe operational workflow: initialize a managed source checkout, validate declared configurations, build a normalized runtime tree with decrypted secrets, and reconcile or deploy that tree using `docker compose`.

**Core Value:** The running Docker Compose state for one Unraid host can be reconciled to Git safely, predictably, and without applying invalid or ambiguous configuration.

### Constraints

- **Platform**: Must run within normal Unraid server constraints — cron execution, ramfs-heavy temporary storage, and persistent USB-backed boot media shape file placement and secret-handling decisions
- **Packaging**: Must be a Python project consumable by other `uv` projects via `uv_build` — the package layout and build backend need to support both CLI use and library imports
- **Parsing**: YAML must be parsed with `strictyaml` — configuration handling should avoid ad hoc parsing and keep validation deterministic
- **Secrets**: Decrypted secret material must only exist in intentionally generated runtime trees — defaults and docs should discourage persisting plaintext secrets on non-ephemeral storage
- **Operations**: `git` and `docker compose` CLI behavior are part of the runtime contract — command execution needs clear error surfaces, dry-run support, and testable wrappers
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.13 - Entire codebase; specified in `pyproject.toml` (line 6) as minimum requirement
- None detected
## Runtime
- Python 3.13 (see `.python-version`)
- pip (via Python standard packaging tools)
- Lockfile: Not detected (no `requirements.txt`, `poetry.lock`, or `uv.lock`)
## Frameworks
- None — no web framework, CLI framework, or application framework detected
- Not present
- setuptools (implicit via `pyproject.toml` PEP 517/518 packaging)
## Key Dependencies
- None — `pyproject.toml` declares `dependencies = []` (line 7)
- None
## Configuration
- `pyproject.toml` defines project metadata (line 1-7):
- Standard Python packaging via `pyproject.toml` (PEP 517/518 compliant)
## Platform Requirements
- Python 3.13 or newer
- No virtual environment configured (`.venv` listed in `.gitignore` line 10 but not present)
- Python 3.13 runtime only
- No deployment automation or containerization detected
## Project State
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Status
## Naming Patterns
- Module files use lowercase with underscores: `main.py` (observed)
- No other modules exist yet for comparison
- Current pattern: lowercase with underscores (see `main()` in `main.py`)
- Expected PEP 8 convention: lowercase with underscores for function and variable names
- No variable naming patterns established yet in codebase
- Standard Python convention (PEP 8) would use `snake_case`
- No type hints are currently used in `main.py`
- Project targets Python 3.13+ (from `pyproject.toml`), which supports modern type hints
- Recommended: Use type hints for function signatures and variables as code expands
## Code Style
- No formatter configured (Black, autopep8, etc. not specified in `pyproject.toml`)
- **Recommendation:** Adopt a formatter (Black recommended for consistency in Python projects)
- No linter configured (Flake8, Ruff, Pylint not in `pyproject.toml`)
- **Recommendation:** Add linting configuration to `pyproject.toml` (Ruff is recommended for speed and modern standards)
- `main.py` follows basic PEP 8 structure:
## Import Organization
- No aliases currently used or configured
## Error Handling
- No explicit error handling is present in `main.py`
- All code paths are happy paths
- None yet; empty function body returns implicitly
- Use try/except blocks for operations that may fail (I/O, external API calls, etc.)
- Use specific exception types rather than bare `except Exception`
- Document expected exceptions in docstrings
## Logging
- Uses `print()` for output in `main.py`
- **Not suitable for production code**
- Use Python's `logging` module instead of `print()`
- Configure logging level via environment or config
- Use structured logging format for parsing/analysis
## Comments
- Not yet established in codebase
- Current `main.py` has no comments
- Use comments for "why", not "what" (code should be readable enough to show what)
- Document non-obvious decisions or complex logic
- Use docstrings for all public functions, classes, and modules
## Function Design
- Current function (`main()`) is minimal
- Recommendation: Keep functions focused on a single responsibility, generally < 50 lines per function
- Not yet applicable; current functions have no parameters
- When adding parameters: use type hints (Python 3.13+ capability)
- Current function returns implicitly (None)
- Recommendation: Use explicit return statements; document return type with type hints
## Module Design
- Current structure: `main()` function as public entry point
- No `__all__` declaration present
- **Recommendation:** Add `__all__ = [...]` when module exports are clarified
- Not applicable yet (single file project)
- When growing beyond one module: consider using `__init__.py` files with explicit exports
## Docstrings
- Use Google-style or NumPy-style docstrings for consistency
- Apply to all modules, classes, functions, and methods
- Include Args, Returns, and Raises sections
## Configuration & Secrets
- No configuration system in place
- No secrets management
- Never hardcode configuration or secrets
- Use environment variables for secrets (via `os.environ` or `python-dotenv`)
- Use configuration files for non-sensitive settings (YAML, TOML, JSON)
- Store secrets in `.env` file (add to `.gitignore` - already present)
## Dependencies
- Empty dependencies list in `pyproject.toml`
- Python 3.13+ required
- Specify version constraints: `package>=1.0,<2.0` (pin major version to prevent breaking changes)
- Document why each dependency is needed
- Prefer smaller, focused packages over monolithic frameworks
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Single entry point module (`main.py`)
- No abstraction layers currently
- All dependencies configured via `pyproject.toml`
- Python 3.13+ runtime requirement
- Early-stage project template structure
## Runtime
- Contains: Single `main()` function and module-level execution guard
- Execution: Called when script runs via `python main.py` or through package entry point
- Responsibilities: Top-level application initialization
## Current State
- Location: Root directory
- Files: `main.py` (entry point only)
- No sub-packages or modules yet
- Single file → no module hierarchy currently
- No imports of other modules (empty project state)
- No database layer, no business logic modules, no utilities
## Execution Flow
## Dependencies
- Unraid API client (referenced in project name/purpose)
- Potential async frameworks (asyncio) for actuator control
- Potential configuration management
## Error Handling
- No exception handling
- No logging framework
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
