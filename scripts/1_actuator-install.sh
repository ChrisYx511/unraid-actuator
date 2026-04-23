#!/bin/bash
set -euo pipefail

install_uv() {
    if command -v uv >/dev/null 2>&1; then
        return
    fi

    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        return
    fi

    if command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh
        return
    fi

    echo "error: curl or wget is required to install uv" >&2
    exit 1
}

load_uv_path() {
    if [ -f "${HOME}/.local/bin/env" ]; then
        # shellcheck disable=SC1091
        . "${HOME}/.local/bin/env"
    fi

    export PATH="${HOME}/.local/bin:${PATH}"
    hash -r
}

install_uv
load_uv_path

uv python install 3.13
uv tool install --force --reinstall --python 3.13 git+https://github.com/ChrisYx511/unraid-actuator.git
