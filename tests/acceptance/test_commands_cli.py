from pathlib import Path

from typer.testing import CliRunner

from agentic_framework.cli import app
from agentic_framework.core.initialization import initialize_project
from agentic_framework.core.workflow import WorkflowService

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
    service = WorkflowService(tmp_path)
    service.store.update_workflow("active", "requirements_review")
    service.continue_workflow()
    for output in service.stage_contract().expected_outputs:
        artifact = tmp_path / output
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(f"# {artifact.stem}\n", encoding="utf-8")
        service.register_artifact(output)
    service.complete_stage()

    revision = _invoke("revise", tmp_path, "requirements_review", "Clarify roles")
    review = _invoke("review", tmp_path)
    completed = runner.invoke(app, ["stage", "complete", "--path", str(tmp_path)])
    approval = _invoke("approve", tmp_path, "requirements_review")
    tasks = _invoke("tasks", tmp_path)
    help_result = runner.invoke(app, ["help"])
    requirements = runner.invoke(app, ["requirements", "--path", str(tmp_path)])

    assert revision.exit_code == 0
    assert "requirements_review: revision_requested" in review.stdout
    assert completed.exit_code == 0
    assert "Approved: requirements_review" in approval.stdout
    assert tasks.stdout == "No tasks recorded.\n"
    assert "/resume" in help_result.stdout
    assert requirements.stdout == "No requirements version has been published.\n"


def test_commands_fail_cleanly_before_initialization(tmp_path: Path) -> None:
    result = _invoke("status", tmp_path)

    assert result.exit_code == 2
    assert "run adt init" in result.stderr
    assert "Traceback" not in result.stderr


def test_stage_and_artifact_control_commands(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    started = _invoke("start", tmp_path)
    shown = runner.invoke(app, ["stage", "show", "--path", str(tmp_path)])
    empty = runner.invoke(
        app,
        ["artifact", "list", "--stage", "project_discovery", "--path", str(tmp_path)],
    )
    missing = runner.invoke(
        app,
        ["artifact", "register", "docs/discovery/project-overview.md", "--path", str(tmp_path)],
    )

    overview = tmp_path / "docs/discovery/project-overview.md"
    overview.write_text("# Overview\n", encoding="utf-8")
    registered = runner.invoke(
        app,
        ["artifact", "register", "docs/discovery/project-overview.md", "--path", str(tmp_path)],
    )
    listed = runner.invoke(app, ["artifact", "list", "--path", str(tmp_path)])
    failed = runner.invoke(
        app, ["stage", "fail", "analysis command failed", "--path", str(tmp_path)]
    )
    status = _invoke("status", tmp_path)
    invalid_stage = runner.invoke(
        app, ["stage", "show", "not-a-stage", "--path", str(tmp_path)]
    )

    assert "Current task:" in started.stdout
    assert "Stage: project_discovery" in shown.stdout
    assert "No artifacts registered" in empty.stdout
    assert missing.exit_code == 2 and "regular project file" in missing.stderr
    assert registered.exit_code == 0 and "SHA-256:" in registered.stdout
    assert "docs/discovery/project-overview.md" in listed.stdout
    assert failed.exit_code == 0 and "Execution: failed" in failed.stdout
    assert "Error: analysis command failed" in status.stdout
    assert invalid_stage.exit_code == 2 and "unknown workflow stage" in invalid_stage.stderr


def test_blocked_stage_and_command_errors_are_actionable(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    _invoke("start", tmp_path)
    blocked = runner.invoke(
        app,
        [
            "stage",
            "fail",
            "Product owner response required",
            "--blocked",
            "--path",
            str(tmp_path),
        ],
    )
    status = _invoke("status", tmp_path)
    wrong_artifact_stage = runner.invoke(
        app,
        [
            "artifact",
            "register",
            "AGENTS.md",
            "--stage",
            "requirements_analysis",
            "--path",
            str(tmp_path),
        ],
    )
    invalid_approval = _invoke("approve", tmp_path, "project_discovery")

    assert blocked.exit_code == 0 and "Execution: blocked" in blocked.stdout
    assert "Blocker: Product owner response required" in status.stdout
    assert wrong_artifact_stage.exit_code == 2
    assert "only be registered for the current" in wrong_artifact_stage.stderr
    assert invalid_approval.exit_code == 2 and "not an approval gate" in invalid_approval.stderr


def test_custom_slash_command_and_current_task_are_persisted(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    _invoke("start", tmp_path)

    created = runner.invoke(
        app,
        [
            "command",
            "create",
            "verify-api",
            "Run current-stage API verification without skipping gates.",
            "--path",
            str(tmp_path),
        ],
    )
    listed = runner.invoke(app, ["command", "list", "--path", str(tmp_path)])
    task = runner.invoke(
        app,
        ["stage", "task", "verify-api: inspect discovery inputs", "--path", str(tmp_path)],
    )
    status = _invoke("status", tmp_path)
    duplicate = runner.invoke(
        app,
        ["command", "create", "verify-api", "Replace", "--path", str(tmp_path)],
    )

    assert created.exit_code == 0 and "Created command: /verify-api" in created.stdout
    assert "/continue:" in listed.stdout
    assert "/verify-api:" in listed.stdout
    assert task.exit_code == 0
    assert "Current task: verify-api: inspect discovery inputs" in status.stdout
    assert duplicate.exit_code == 2 and "preserved" in duplicate.stderr
