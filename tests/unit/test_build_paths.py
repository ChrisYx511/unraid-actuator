from pathlib import Path

import pytest

from unraid_actuator.build_paths import (
    BUILD_MARKER_NAME,
    DEFAULT_BUILD_ROOT,
    create_stage_root,
    resolve_output_root,
    validate_output_root,
)


def test_default_build_root_resolves_to_tmp_path() -> None:
    assert resolve_output_root(None) == DEFAULT_BUILD_ROOT
    assert BUILD_MARKER_NAME == ".UNRAID_RUNNING_CONFIGURATION"


def test_custom_output_path_must_be_empty_or_missing(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing"
    validate_output_root(missing_path)

    empty_path = tmp_path / "empty"
    empty_path.mkdir()
    validate_output_root(empty_path)


def test_non_default_non_empty_path_fails_before_build(tmp_path: Path) -> None:
    custom_root = tmp_path / "custom"
    custom_root.mkdir()
    (custom_root / "existing").write_text("busy\n", encoding="utf-8")

    with pytest.raises(ValueError):
        validate_output_root(custom_root)


def test_stage_root_is_created_as_sibling(tmp_path: Path) -> None:
    final_root = tmp_path / "output" / "build"
    stage_root = create_stage_root(final_root)

    assert stage_root.parent == final_root.parent
    assert stage_root.exists()
