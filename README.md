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

## Unraid bootstrap scripts

The repository includes example shell scripts for first-time Unraid setup:

- `scripts/1_actuator-install.sh` installs `uv`, installs Python 3.13 through `uv`, and installs `unraid-actuator` as a uv-managed tool.
- `scripts/4_actuator-init.sh.template` shows one way to copy EJSON keys into `/opt/ejson/keys`, initialize the actuator, validate the configured host, and build the runtime tree without any extra secret-key environment variable.
