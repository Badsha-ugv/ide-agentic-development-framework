from pathlib import Path

from typer.testing import CliRunner

from agentic_framework.cli import app
from agentic_framework.core.intelligence import analyze_existing_project, analyze_impact

runner = CliRunner()


def test_analyze_existing_project_detects_dependencies_modules_and_todos(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "shop"\ndependencies = ["fastapi>=0.110", "pytest>=8.0"]\n',
        encoding="utf-8",
    )
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "customers.py").write_text(
        "# TODO: add CSV export\ndef list_customers():\n    return []\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_customers.py").write_text(
        "def test_list_customers():\n    assert True\n",
        encoding="utf-8",
    )

    report = analyze_existing_project(tmp_path)
    assert "python" in report.dependencies
    assert "fastapi" in report.dependencies["python"]
    assert "app" in report.modules
    assert "pytest" in report.test_runners
    assert report.todo_count == 1
    assert "app/customers.py:1" in report.todo_samples[0]

    impact = analyze_impact(tmp_path, "Add Excel export for customers")
    assert "app/customers.py" in impact.matched_files
    assert "tests/test_customers.py" in impact.related_tests


def test_analyze_cli_with_focus_prints_impact(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^19.0.0"}, "devDependencies": {"vitest": "^2.0.0"}}',
        encoding="utf-8",
    )
    (tmp_path / "src" / "components").mkdir(parents=True)
    (tmp_path / "src" / "components" / "BillingPanel.tsx").write_text(
        "export function BillingPanel() { return null; }\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app, ["analyze", "--path", str(tmp_path), "--focus", "Update billing panel"]
    )
    assert result.exit_code == 0
    assert "Test runners: vitest" in result.stdout
    assert "src/components/BillingPanel.tsx" in result.stdout
