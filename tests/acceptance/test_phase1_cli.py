from pathlib import Path

from typer.testing import CliRunner

from agentic_framework.cli import app
from agentic_framework.core.initialization import initialize_project

runner = CliRunner()


def test_phase1_cli_commands_report_project_plan_and_agents(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    initialize_project(tmp_path, initialize_git=False)

    analyze_res = runner.invoke(app, ["analyze", "--path", str(tmp_path)])
    assert analyze_res.exit_code == 0
    assert "Technologies: Python" in analyze_res.stdout

    plan_res = runner.invoke(app, ["plan", "--path", str(tmp_path)])
    assert plan_res.exit_code == 0
    assert "Complexity:" in plan_res.stdout
    assert "Planned stages:" in plan_res.stdout

    test_res = runner.invoke(app, ["test", "--path", str(tmp_path)])
    assert test_res.exit_code == 0
    assert "Validation criteria:" in test_res.stdout

    docs_res = runner.invoke(app, ["docs", "--path", str(tmp_path)])
    assert docs_res.exit_code == 0
    assert "Expected outputs:" in docs_res.stdout

    agents_res = runner.invoke(app, ["agents", "--path", str(tmp_path)])
    assert agents_res.exit_code == 0
    assert "ui_ux_designer: UI/UX Designer" in agents_res.stdout
    assert "documentation_engineer: Documentation Engineer" in agents_res.stdout
