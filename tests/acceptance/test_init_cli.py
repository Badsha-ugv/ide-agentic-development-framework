from pathlib import Path

from typer.testing import CliRunner

from agentic_framework.cli import app

runner = CliRunner()


def test_cli_initializes_project_and_is_repeatable(tmp_path: Path) -> None:
    target = tmp_path / "application"

    first = runner.invoke(app, ["init", "--path", str(target), "--no-git"])
    second = runner.invoke(app, ["init", "--path", str(target), "--no-git"])

    assert first.exit_code == 0
    assert "Project mode: new" in first.stdout
    assert "Created files: 24" in first.stdout
    assert second.exit_code == 0
    assert "Created files: 0" in second.stdout
    assert "Conflicts: 0" in second.stdout
    assert (target / "AGENTS.md").is_file()
    assert (target / ".agentic" / "config.yaml").is_file()


def test_cli_reports_invalid_target_without_traceback(tmp_path: Path) -> None:
    target = tmp_path / "file"
    target.write_text("content", encoding="utf-8")

    result = runner.invoke(app, ["init", "--path", str(target), "--no-git"])

    assert result.exit_code == 2
    assert "initialization target is not a directory" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_supports_mode_and_task_flags(tmp_path: Path) -> None:
    target = tmp_path / "existing-app"
    target.mkdir()
    (target / "package.json").write_text("{}", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "init",
            "--path",
            str(target),
            "--mode",
            "existing",
            "--task",
            "security_audit",
            "--no-git",
        ],
    )
    assert result.exit_code == 0
    assert "Project mode: existing" in result.stdout
    assert "Session task: security_audit" in result.stdout

