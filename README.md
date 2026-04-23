# unraid-actuator

`unraid-actuator` is a `uv`-buildable Python package and CLI for reconciling a single Unraid host's Docker Compose state against a Git-managed infrastructure repository. It validates the checked-out host tree, builds an actuator-managed runtime tree, and can deploy, tear down, or reconcile that runtime state on the target host.

## Prerequisites

`unraid-actuator` expects these dependencies to be available on the host:

- **Python 3.13 or newer** — required by the package metadata and toolchain. See the [Python 3.13 documentation](https://docs.python.org/3.13/).
- **Git** — used to clone and update the managed infrastructure checkout. See the [Git documentation](https://git-scm.com/doc).
- **EJSON** — used to decrypt `secret-env.ejson` with host key material stored under `/opt/ejson/keys`. See the [EJSON project documentation](https://github.com/Shopify/ejson).
- **Docker Compose v2** — invoked through `docker compose` for validation, deploy, teardown, and reconcile workflows. See the [Docker Compose documentation](https://docs.docker.com/compose/).

For the installation flow shown below, you will also want [`uv`](https://docs.astral.sh/uv/) available on the host.

## Installation

Install `unraid-actuator` as a uv-managed tool:

```bash
uv python install 3.13
uv tool install --python 3.13 git+https://github.com/ChrisYx511/unraid-actuator.git
```

After installation, the CLI is available as:

```bash
unraid-actuator --help
```

If you are working from a local checkout instead of installing the tool globally:

```bash
uv sync --group dev
uv run unraid-actuator --help
```

## Expected source repository layout

The managed infrastructure repository is host-centric. Each host directory contains an app declaration file, encrypted secrets, and one or more app/environment directories:

```text
<repo>/
└── <host>/
    ├── apps.yaml
    ├── secret-env.ejson
    └── <app>/
        └── <environment>/
            ├── docker-compose.yaml
            ├── .env
            ├── template.yaml
            ├── values.yaml
            └── other files referenced by docker compose
```

Supported inputs per environment:

- One static compose file: `docker-compose.yaml` or `docker-compose.yml`
- Or one template descriptor: `template.yaml` or `template.yml`
- When templated, one matching values file: `values.yaml` or `values.yml`
- Optional `.env`
- Additional files or directories referenced by Compose, such as bind-mounted config files, `env_file` inputs, or template fragments

Each host must also declare the environments that are considered active in `apps.yaml` or `apps.yml`. If both extensions exist for the same logical file, validation fails rather than guessing. During `build`, the actuator copies the entire environment directory into the output tree and then writes the normalized `docker-compose.yaml` and merged `.env` used for deployment.

## Typical operator workflow

The usual lifecycle on an Unraid host is:

1. Install the tool and host prerequisites.
2. Copy EJSON key material into `/opt/ejson/keys`.
3. Run `unraid-actuator init` once for the target repository and host.
4. Run `unraid-actuator validate` to confirm the current checkout is buildable.
5. Run `unraid-actuator build` to materialize the runtime tree.
6. Run `unraid-actuator deploy` to apply that built tree, or `unraid-actuator reconcile` to fetch, validate, build, and apply the configured deploy branch in one flow.

## Command usage

### `init`

Configure the managed repository checkout for the current host:

```bash
unraid-actuator init \
  --repo-url "https://github.com/example/infrastructure.git" \
  --deploy-branch "main" \
  --hostname "tower" \
  --source-path "/mnt/user/appdata/unraid-actuator/source"
```

This stores the active configuration and clones the repository if the managed checkout path is empty.

### `validate`

Validate the configured host tree:

```bash
unraid-actuator validate
```

Validate one specific app/environment pair:

```bash
unraid-actuator validate --app nextcloud --environment production
```

### `build`

Build a normalized runtime tree for the configured host:

```bash
unraid-actuator build
```

Build into a custom output path:

```bash
unraid-actuator build --output-path /dev/shm/unraid-actuator/build
```

The default output path is `/tmp/unraid-actuator/build`. A tmpfs or ram-backed path is strongly recommended because the built `.env` files contain decrypted secret material.

### `deploy`

Deploy the default built runtime tree:

```bash
unraid-actuator deploy
```

Deploy one scoped target:

```bash
unraid-actuator deploy --app nextcloud --environment production
```

If you built into a non-default location, pass `--build-root`.

### `teardown`

Tear down the default built runtime tree:

```bash
unraid-actuator teardown
```

Tear down one scoped target:

```bash
unraid-actuator teardown --app nextcloud --environment production
```

### `reconcile`

Fetch, validate, build, and apply the configured deploy branch:

```bash
unraid-actuator reconcile
```

Preview external actions without mutating the managed source or runtime tree:

```bash
unraid-actuator reconcile --dry-run
```

### Global dry-run mode

The CLI also supports a top-level `--dry-run` flag that prints external actions without executing them:

```bash
unraid-actuator --dry-run build
```

## Unraid bootstrap scripts

The repository includes example shell scripts for first-time Unraid setup:

- `scripts/1_actuator-install.sh` installs `uv`, installs Python 3.13 through `uv`, and installs `unraid-actuator` as a uv-managed tool.
- `scripts/4_actuator-init.sh.template` shows one way to copy EJSON keys into `/opt/ejson/keys`, initialize the actuator, validate the configured host, and build the runtime tree.

Treat these scripts as starting points and replace the placeholder repository and host values before using them on a real server.

## Developer workflow

Install the project and development tooling:

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
