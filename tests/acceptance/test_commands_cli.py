from pathlib import Path

from typer.testing import CliRunner

from agentic_framework.cli import app
from agentic_framework.core.initialization import initialize_project

runner = CliRunner()


def _invoke(command: str, root: Path, *arguments: str):
    return runner.invoke(app, [command, *arguments, "--path", str(root)])


def test_lifecycle_commands_persist_and_recover(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)

    started = _invoke("start", tmp_path)
    advanced = _invoke("continue", tmp_path)
    paused = _invoke("pause", tmp_path)
    status = _invoke("status", tmp_path)
    resumed = _invoke("resume", tmp_path)
    stopped = _invoke("stop", tmp_path)

    assert started.exit_code == 0 and "Status: active" in started.stdout
    assert advanced.exit_code == 0 and "Stage: project_discovery" in advanced.stdout
    assert paused.exit_code == 0 and "Status: paused" in paused.stdout
    assert status.exit_code == 0 and "Stage: project_discovery" in status.stdout
    assert resumed.exit_code == 0 and "Status: active" in resumed.stdout
    assert stopped.exit_code == 0 and "Status: stopped" in stopped.stdout


def test_review_approval_revision_help_tasks_and_requirements_commands(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)

    revision = _invoke("revise", tmp_path, "requirements_review", "Clarify roles")
    review = _invoke("review", tmp_path)
    approval = _invoke("approve", tmp_path, "requirements_review")
    tasks = _invoke("tasks", tmp_path)
    help_result = runner.invoke(app, ["help"])
    requirements = runner.invoke(app, ["requirements", "--path", str(tmp_path)])

    assert revision.exit_code == 0
    assert "requirements_review: revision_requested" in review.stdout
    assert "Approved: requirements_review" in approval.stdout
    assert tasks.stdout == "No tasks recorded.\n"
    assert "/resume" in help_result.stdout
    assert requirements.stdout == "No requirements version has been published.\n"


def test_commands_fail_cleanly_before_initialization(tmp_path: Path) -> None:
    result = _invoke("status", tmp_path)

    assert result.exit_code == 2
    assert "run adt init" in result.stderr
    assert "Traceback" not in result.stderr
