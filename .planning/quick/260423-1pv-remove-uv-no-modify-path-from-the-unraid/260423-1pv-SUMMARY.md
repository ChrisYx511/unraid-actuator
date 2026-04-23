# Quick Task 260423-1pv Summary

**Description:** Remove UV_NO_MODIFY_PATH from the Unraid install script  
**Date:** 2026-04-23  
**Implementation commit:** `01ba9d4`

## Outcome

- Removed `UV_NO_MODIFY_PATH=1` from both the `curl` and `wget` installer paths in `scripts/1_actuator-install.sh`.
- Preserved the rest of the Unraid boot workflow, including the explicit PATH reload after uv installation.

## Verification commands

```bash
bash -n scripts/1_actuator-install.sh
uv run pytest -q
uv build
uv run ruff check .
uv run basedpyright
```

## Notes

- This change lets the uv installer update PATH on the Unraid host as intended, instead of forcing the no-modify-path mode.
