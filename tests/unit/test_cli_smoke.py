import pytest

from unraid_actuator import build_parser, main


def test_parser_help_exposes_init_and_dry_run() -> None:
    help_text = build_parser().format_help()

    assert "init" in help_text
    assert "--dry-run" in help_text


def test_main_help_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])

    assert excinfo.value.code == 0
    assert "unraid-actuator" in capsys.readouterr().out


def test_package_exports_main() -> None:
    assert callable(main)
