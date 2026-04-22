# Technology Stack

**Analysis Date:** 2025-01-10

## Languages

**Primary:**
- Python 3.13 - Entire codebase; specified in `pyproject.toml` (line 6) as minimum requirement

**Secondary:**
- None detected

## Runtime

**Environment:**
- Python 3.13 (see `.python-version`)

**Package Manager:**
- pip (via Python standard packaging tools)
- Lockfile: Not detected (no `requirements.txt`, `poetry.lock`, or `uv.lock`)

## Frameworks

**Core:**
- None — no web framework, CLI framework, or application framework detected

**Testing:**
- Not present

**Build/Dev:**
- setuptools (implicit via `pyproject.toml` PEP 517/518 packaging)

## Key Dependencies

**Critical:**
- None — `pyproject.toml` declares `dependencies = []` (line 7)

**Infrastructure:**
- None

## Configuration

**Environment:**
- `pyproject.toml` defines project metadata (line 1-7):
  - Name: `unraid-actuator`
  - Version: `0.1.0`
  - Python requirement: `>=3.13`
  - No external dependencies

**Build:**
- Standard Python packaging via `pyproject.toml` (PEP 517/518 compliant)

## Platform Requirements

**Development:**
- Python 3.13 or newer
- No virtual environment configured (`.venv` listed in `.gitignore` line 10 but not present)

**Production:**
- Python 3.13 runtime only
- No deployment automation or containerization detected

## Project State

This is an **empty scaffolding project** — `main.py` contains only a stub entrypoint (`main()` function that prints a greeting). No actual implementation, dependencies, or infrastructure code exists. Suitable for starting a new application but not yet functional.

---

*Stack analysis: 2025-01-10*
