from pathlib import Path

from typer.testing import CliRunner

from agentic_framework.cli import app

runner = CliRunner()


def test_requirements_cli_creates_version_impact_report_and_detects_duplicate(
    tmp_path: Path,
) -> None:
    inbox = tmp_path / "requirements" / "inbox"
    inbox.mkdir(parents=True)
    source = inbox / "requirements.md"
    source.write_text("REQ-001: Initial\n", encoding="utf-8")

    first = runner.invoke(app, ["requirements", "ingest", "--path", str(tmp_path)])
    source.write_text("REQ-001: Revised\nREQ-002: Added\n", encoding="utf-8")
    second = runner.invoke(app, ["requirements", "ingest", "--path", str(tmp_path)])
    duplicate = runner.invoke(app, ["requirements", "ingest", "--path", str(tmp_path)])

    assert first.exit_code == 0
    assert "Created version-001 from 1 source file(s)." in first.stdout
    assert second.exit_code == 0
    assert "Created version-002" in second.stdout
    assert "reports/version-001-to-version-002-impact.md" in second.stdout
    assert duplicate.exit_code == 0
    assert "No changes; inbox matches version-002." in duplicate.stdout


def test_requirements_cli_reports_empty_inbox_without_traceback(tmp_path: Path) -> None:
    result = runner.invoke(app, ["requirements", "ingest", "--path", str(tmp_path)])

    assert result.exit_code == 2
    assert "no requirement files found" in result.stderr
    assert "Traceback" not in result.stderr
