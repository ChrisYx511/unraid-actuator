# Codebase Structure

**Analysis Date:** 2025-01-15

## Directory Layout

```
unraid-actuator/
├── main.py           # Application entry point
├── pyproject.toml    # Project metadata and dependency configuration
├── README.md         # Project documentation
├── .gitignore        # Git exclusion rules
├── .python-version   # Python version specification (3.13)
└── .git/             # Version control
```

## Key File Locations

**Entry Points:**
- `main.py`: Primary executable. Defines `main()` function and runs when executed as a script.

**Configuration:**
- `pyproject.toml`: Project metadata, Python version requirement (>=3.13), and dependency declarations
- `.python-version`: Python runtime version pinning (currently 3.13)

**Build/Environment:**
- `.gitignore`: Excludes `__pycache__/`, `.venv/`, build artifacts, and `.egg-info/`

## Current File Purposes

**`main.py`:**
- 6 lines of code
- Contains single entry point function
- Uses standard Python if-name guard pattern
- No external imports currently

**`pyproject.toml`:**
- Standard Python packaging format (PEP 517/518)
- Project name: `unraid-actuator`
- Version: `0.1.0`
- No runtime dependencies yet (empty `dependencies` list)

## Where to Add New Code

**New Modules (When Needed):**
- Create subdirectory at repository root (e.g., `src/unraid_actuator/` or `unraid_actuator/`)
- Move logic into:
  - `services/` — Unraid API client and actuator control logic
  - `models/` — Data classes for devices, states
  - `config/` — Configuration loading and management
  - `cli/` — Command-line interface if expanding beyond single entry point

**Adding Dependencies:**
- Edit `pyproject.toml` → `dependencies` list
- Examples: `requests` (HTTP), `aiohttp` (async HTTP), `python-dotenv` (config)

**Adding Tests:**
- Create `tests/` directory at root
- Use file pattern: `test_<module>.py` or `<module>_test.py`
- Configure test runner in `pyproject.toml` under `[tool.pytest]` or `[tool.unittest]`

**Utilities and Helpers:**
- If small: Add to `main.py` or create `utils.py`
- If organized: Create `utils/` directory with focused modules

## Naming Conventions

**Files:**
- All lowercase with underscores: `main.py`, `api_client.py`, `device_models.py`
- Test files: `test_<module>.py`

**Modules/Packages:**
- Snake case: `unraid_actuator`, `device_manager`

**Functions:**
- Snake case: `main()`, `get_device_status()`, `control_actuator()`

**Classes:**
- PascalCase: `UnraidClient`, `ActuatorDevice`, `DeviceConfig`

## Special Directories

**`.git/`:**
- Git repository metadata
- Contains version history and branch information

**`.venv/` (when created):**
- Python virtual environment (created by `python -m venv .venv`)
- Listed in `.gitignore` — not committed
- Contains isolated Python interpreter and installed packages

---

*Structure analysis: 2025-01-15*
