# unraid-actuator

`unraid-actuator` is a `uv`-buildable Python package and CLI for reconciling a single Unraid host's Docker Compose state against a Git-managed infrastructure repository.

## Developer workflow

Install the project and dev tools:

```bash
uv sync --group dev
```

Run the current verification stack:

```bash
uv run pytest -q
uv run ruff format .
uv run ruff check .
uv run basedpyright
```

`basedpyright` runs in strict mode over `src/`. Ruff linting and formatting run across the repository.
