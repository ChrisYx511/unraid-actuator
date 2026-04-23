# Quick Task 260422-xbd: Remove __future__ annotations imports and replace deprecated typing imports with modern Python 3.13 equivalents

## Goal

Modernize import usage for Python 3.13 by removing unnecessary `from __future__ import annotations` lines and replacing deprecated typing aliases with current equivalents, while keeping behavior unchanged.

## Tasks

1. **Remove redundant future imports**
   - Files: `src/**/*.py`, `tests/**/*.py`
   - Action: Delete `from __future__ import annotations` where it is no longer needed for the current annotation syntax in this codebase.
   - Verify: The package and tests still import and run cleanly.
   - Done when: No Python files in the repo still contain that future import.

2. **Replace deprecated typing aliases**
   - Files: targeted typing-import users in `src/`
   - Action: Swap any deprecated typing aliases to modern Python 3.13 equivalents without widening scope beyond the actual deprecated imports present.
   - Verify: Ruff, basedpyright, tests, and build all stay green.
   - Done when: Deprecated typing imports in the touched files are removed and the repo remains clean under existing checks.
