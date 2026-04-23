from __future__ import annotations

from pathlib import Path

import pytest

from unraid_actuator.reconcile_lock import acquire_reconcile_lock


def test_second_lock_acquire_fails_immediately(tmp_path: Path) -> None:
    lock_path = tmp_path / "reconcile.lock"

    with acquire_reconcile_lock(lock_path):
        with pytest.raises(ValueError, match="another reconcile is already active"):
            with acquire_reconcile_lock(lock_path):
                pass


def test_lock_releases_after_exception(tmp_path: Path) -> None:
    lock_path = tmp_path / "reconcile.lock"

    with pytest.raises(RuntimeError, match="boom"):
        with acquire_reconcile_lock(lock_path):
            raise RuntimeError("boom")

    with acquire_reconcile_lock(lock_path):
        assert lock_path.read_text(encoding="utf-8").startswith("pid=")


def test_same_lock_helper_serializes_dry_run_and_live_reconcile_calls(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "reconcile.lock"

    with acquire_reconcile_lock(lock_path):
        with pytest.raises(ValueError, match="another reconcile is already active"):
            with acquire_reconcile_lock(lock_path):
                pass
