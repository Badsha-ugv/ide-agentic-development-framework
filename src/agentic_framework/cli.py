"""Command-line interface for the Agentic Development Framework."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agentic_framework import __version__
from agentic_framework.core.command_registry import COMMANDS
from agentic_framework.core.config import dump_config, load_config
from agentic_framework.core.custom_commands import create_custom_command, custom_commands
from agentic_framework.core.initialization import FileStatus, initialize_project
from agentic_framework.core.workflow import WorkflowService
from agentic_framework.exceptions import (
    ConfigurationError,
    InitializationError,
    RequirementsError,
    StateError,
)
from agentic_framework.requirements_manager import RequirementsManager

app = typer.Typer(
    name="adt",
    help="Local-first agentic development workflow tooling.",
    no_args_is_help=True,
)
config_app = typer.Typer(help="Inspect and validate framework configuration.")
requirements_app = typer.Typer(
    help="Show, version, and compare project requirements.", invoke_without_command=True
)
stage_app = typer.Typer(help="Inspect, complete, or fail the current execution stage.")
artifact_app = typer.Typer(help="Register and inspect stage deliverables.")
command_app = typer.Typer(help="Create and inspect ADF-aware Antigravity slash commands.")
app.add_typer(config_app, name="config")
app.add_typer(requirements_app, name="requirements")
app.add_typer(stage_app, name="stage")
app.add_typer(artifact_app, name="artifact")
app.add_typer(command_app, name="command")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"adt {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = None,
) -> None:
    """Run Agentic Development Framework commands."""


@app.command("init")
def init_project(
    path: Annotated[
        Path,
        typer.Option("--path", help="Project directory to initialize."),
    ] = Path("."),
    initialize_git: Annotated[
        bool,
        typer.Option("--git/--no-git", help="Initialize Git when no repository is detected."),
    ] = True,
) -> None:
    """Safely initialize ADF in a new or existing project."""

    try:
        result = initialize_project(path, initialize_git=initialize_git)
    except InitializationError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    created = sum(item.status is FileStatus.CREATED for item in result.files)
    typer.echo(f"Initialized {result.inspection.root}")
    typer.echo(f"Project mode: {result.mode.value}")
    typer.echo(f"Created files: {created}")
    typer.echo(f"Conflicts: {len(result.conflicts)}")
    typer.echo("Report: .agentic/reports/initialization.md")


def _workflow_action(path: Path, action: str) -> None:
    try:
        service = WorkflowService(path)
        result = getattr(service, action)()
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Status: {result['status']}")
    typer.echo(f"Stage: {result['current_stage']}")
    execution = result.get("execution")
    if execution:
        typer.echo(f"Execution: {execution['status']}")
        if execution.get("current_task"):
            typer.echo(f"Current task: {execution['current_task']}")
        typer.echo(f"Attempts: {execution['attempt_count']}")
        if execution.get("blocker"):
            typer.echo(f"Blocker: {execution['blocker']}")
        if execution.get("error"):
            typer.echo(f"Error: {execution['error']}")
    if result.get("approval"):
        typer.echo(f"Approval: {result['approval']}")
    contract = result.get("contract")
    if contract:
        typer.echo(f"Objective: {contract['objective']}")
        typer.echo("Expected outputs:")
        for output in contract["expected_outputs"]:
            typer.echo(f"- {output}")
        typer.echo(f"Contract: {result['contract_file']}")


@app.command("start")
def start(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """Start the persisted workflow."""

    _workflow_action(path, "start")


@app.command("status")
def status(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """Show persisted workflow status."""

    _workflow_action(path, "status")


@app.command("pause")
def pause(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """Pause safely and create a checkpoint."""

    _workflow_action(path, "pause")


@app.command("resume")
def resume(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """Validate the latest checkpoint and resume."""

    _workflow_action(path, "resume")


@app.command("continue")
def continue_command(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """Prepare or resume the current stage without advancing it."""

    _workflow_action(path, "continue_workflow")


@app.command("stop")
def stop(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """Stop safely and create a checkpoint."""

    _workflow_action(path, "stop")


@app.command("help")
def help_command() -> None:
    """List conversational and CLI framework commands."""

    for name, description in COMMANDS.items():
        typer.echo(f"/{name}: {description}")


@app.command("tasks")
def tasks(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """List persisted workflow tasks."""

    try:
        values = WorkflowService(path).store.tasks()
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    if not values:
        typer.echo("No tasks recorded.")
    for task in values:
        typer.echo(f"{task['task_id']} [{task['status']}] {task['title']}")


@app.command("review")
def review(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """List items awaiting approval or revision."""

    try:
        service = WorkflowService(path)
        values = service.store.approvals()
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    pending = [item for item in values if item["status"] != "approved"]
    if not pending:
        typer.echo("No deliverables waiting for review.")
    for item in pending:
        typer.echo(f"{item['stage_id']}: {item['status']}")
        for artifact in service.store.artifacts(item["stage_id"]):
            typer.echo(f"- {artifact['path']} (revision {artifact['revision']})")


@app.command("approve")
def approve(
    stage: Annotated[str, typer.Argument(help="Workflow stage ID to approve.")],
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Record explicit approval for a stage."""

    try:
        service = WorkflowService(path)
        result = service.approve(stage)
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Approved: {stage}")
    typer.echo(f"Stage: {result['current_stage']}")


@app.command("revise")
def revise(
    stage: Annotated[str, typer.Argument(help="Workflow stage ID to revise.")],
    feedback: Annotated[str, typer.Argument(help="Revision feedback.")],
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Record revision feedback for a stage."""

    try:
        service = WorkflowService(path)
        result = service.revise(stage, feedback)
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Revision requested: {stage}")
    typer.echo(f"Execution: {result['execution']['status']}")


@stage_app.command("show")
def show_stage(
    stage: Annotated[str | None, typer.Argument(help="Stage ID; defaults to current.")] = None,
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Show the structured execution contract for a stage."""

    try:
        service = WorkflowService(path)
        contract = service.stage_contract(stage)
        current = service.status()
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Stage: {contract.id}")
    typer.echo(f"Objective: {contract.objective}")
    if contract.id == current["current_stage"]:
        typer.echo(f"Execution: {current['execution']['status']}")
    typer.echo("Expected outputs:")
    for output in contract.expected_outputs:
        typer.echo(f"- {output}")


@stage_app.command("complete")
def complete_stage(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """Validate registered outputs and complete the current stage."""

    _workflow_action(path, "complete_stage")


@stage_app.command("fail")
def fail_stage(
    message: Annotated[str, typer.Argument(help="Actionable failure or blocker detail.")],
    blocked: Annotated[
        bool, typer.Option("--blocked", help="Record an external blocker instead of a failure.")
    ] = False,
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Persist a stage failure or blocker without advancing."""

    try:
        result = WorkflowService(path).fail_stage(message, blocked=blocked)
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Stage: {result['current_stage']}")
    typer.echo(f"Execution: {result['execution']['status']}")


@stage_app.command("task")
def set_stage_task(
    description: Annotated[str, typer.Argument(help="Current IDE-agent task description.")],
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Persist the current stage-scoped IDE-agent task."""

    try:
        result = WorkflowService(path).set_current_task(description)
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Stage: {result['current_stage']}")
    typer.echo(f"Current task: {result['execution']['current_task']}")


@artifact_app.command("register")
def register_artifact(
    artifact_path: Annotated[str, typer.Argument(help="Project-relative deliverable path.")],
    stage: Annotated[str | None, typer.Option("--stage")] = None,
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Register the current bytes of a stage deliverable."""

    try:
        artifact = WorkflowService(path).register_artifact(artifact_path, stage)
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Registered: {artifact['path']}")
    typer.echo(f"Stage: {artifact['stage_id']}")
    typer.echo(f"Revision: {artifact['revision']}")
    typer.echo(f"SHA-256: {artifact['sha256']}")


@artifact_app.command("list")
def list_artifacts(
    stage: Annotated[str | None, typer.Option("--stage")] = None,
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """List current registered artifact revisions."""

    try:
        service = WorkflowService(path)
        values = service.store.artifacts(stage)
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    if not values:
        typer.echo("No artifacts registered.")
    for artifact in values:
        typer.echo(
            f"{artifact['stage_id']}: {artifact['path']} "
            f"(revision {artifact['revision']}, {artifact['sha256']})"
        )


@command_app.command("create")
def create_command(
    name: Annotated[str, typer.Argument(help="Slash-command name without the leading slash.")],
    instructions: Annotated[str, typer.Argument(help="Project-specific command instructions.")],
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Create a non-overwriting, stage-aware Antigravity workspace skill."""

    try:
        command = create_custom_command(path, name, instructions)
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Created command: /{command.name}")
    typer.echo(f"Skill: {command.path}")


@command_app.command("list")
def list_commands(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """List slash-command skills discoverable in the workspace."""

    values = custom_commands(path)
    if not values:
        typer.echo("No workspace command skills found.")
    for command in values:
        typer.echo(f"/{command.name}: {command.path}")


@config_app.command("validate")
def validate_config(
    path: Annotated[
        Path,
        typer.Argument(help="YAML configuration file to validate.", exists=False),
    ],
) -> None:
    """Validate a YAML configuration file and print its normalized representation."""

    try:
        config = load_config(path)
    except ConfigurationError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(dump_config(config), nl=False)


@requirements_app.callback()
def requirements_status(
    context: typer.Context,
    path: Annotated[Path, typer.Option("--path", help="Project directory.")] = Path("."),
) -> None:
    """Show the latest requirements version when no subcommand is supplied."""

    if context.invoked_subcommand is not None:
        return
    try:
        latest = RequirementsManager(path).latest_version()
    except RequirementsError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    if latest is None:
        typer.echo("No requirements version has been published.")
    else:
        typer.echo(f"Current requirements: {latest['version']}")
        typer.echo(f"Source files: {len(latest['files'])}")


@requirements_app.command("ingest")
def ingest_requirements(
    path: Annotated[
        Path,
        typer.Option("--path", help="Project directory containing requirements/inbox."),
    ] = Path("."),
) -> None:
    """Preserve and publish all files currently in the requirements inbox."""

    try:
        result = RequirementsManager(path).ingest()
    except RequirementsError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    if result.duplicate:
        typer.echo(f"No changes; inbox matches {result.version}.")
        return
    typer.echo(f"Created {result.version} from {result.file_count} source file(s).")
    typer.echo(f"Requirement IDs: {result.requirement_count}")
    if result.impact_report:
        relative_report = result.impact_report.relative_to(result.version_path.parents[1])
        typer.echo(f"Impact report: {relative_report}")

