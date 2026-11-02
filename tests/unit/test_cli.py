from pathlib import Path

from typer.testing import CliRunner

from agentic_framework.cli import app

runner = CliRunner()


def test_cli_reports_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout == "adt 0.1.0\n"


def test_module_cli_has_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Local-first agentic development workflow tooling" in result.stdout
    assert "init" in result.stdout
    assert "config" in result.stdout
    assert "requirements" in result.stdout


def test_validate_config_prints_normalized_yaml(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("project:\n  name: example\n", encoding="utf-8")

    result = runner.invoke(app, ["config", "validate", str(config)])

    assert result.exit_code == 0
    assert "schema_version: 1" in result.stdout
    assert "name: example" in result.stdout


def test_validate_config_has_actionable_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["config", "validate", str(tmp_path / "missing.yaml")])

    assert result.exit_code == 2
    assert "configuration file does not exist" in result.stderr

