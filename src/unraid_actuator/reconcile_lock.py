import fcntl
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_RECONCILE_LOCK_PATH = Path("/tmp/unraid-actuator/reconcile.lock")
_ACTIVE_LOCKS: set[Path] = set()


@contextmanager
def acquire_reconcile_lock(path: Path = DEFAULT_RECONCILE_LOCK_PATH) -> Iterator[Path]:
    resolved_path = path.resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    if resolved_path in _ACTIVE_LOCKS:
        raise ValueError(f"another reconcile is already active: {resolved_path}")

    handle = resolved_path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(f"another reconcile is already active: {resolved_path}") from exc

        _ACTIVE_LOCKS.add(resolved_path)
        handle.seek(0)
        handle.truncate()
        handle.write(f"pid={os.getpid()} acquired_at={datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
        handle.flush()
        yield resolved_path
    finally:
        _ACTIVE_LOCKS.discard(resolved_path)
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


__all__ = ["DEFAULT_RECONCILE_LOCK_PATH", "acquire_reconcile_lock"]
