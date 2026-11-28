"""Command-line interface for the Agentic Development Framework."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
import yaml

from agentic_framework import __version__
from agentic_framework.core.command_registry import COMMANDS
from agentic_framework.core.config import (
    IdeKind,
    ProjectMode,
    ProjectTask,
    TaskComplexity,
    dump_config,
    load_config,
)
from agentic_framework.core.custom_commands import create_custom_command, custom_commands
from agentic_framework.core.evaluation import evaluate_agent_output
from agentic_framework.core.initialization import FileStatus, initialize_project
from agentic_framework.core.intelligence import analyze_existing_project, analyze_impact
from agentic_framework.core.memory import load_project_memory, record_project_decision
from agentic_framework.core.preferences import (
    default_global_preferences_path,
    project_preferences_path,
    reset_preferences_file,
    resolve_effective_preferences,
    update_preference_field,
)
from agentic_framework.core.workflow import WorkflowService
from agentic_framework.exceptions import (
    ConfigurationError,
    InitializationError,
    RequirementsError,
    StateError,
)
from agentic_framework.providers import list_providers
from agentic_framework.requirements_manager import RequirementsManager, ScreenshotManager

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
preferences_app = typer.Typer(
    help="View, update, or reset saved design preferences.",
    invoke_without_command=True,
)
memory_app = typer.Typer(
    help="Inspect project memory and record non-overwriting decisions.",
    invoke_without_command=True,
)
app.add_typer(config_app, name="config")
app.add_typer(requirements_app, name="requirements")
app.add_typer(stage_app, name="stage")
app.add_typer(artifact_app, name="artifact")
app.add_typer(command_app, name="command")
app.add_typer(preferences_app, name="preferences")
app.add_typer(memory_app, name="memory")


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
    mode: Annotated[
        ProjectMode | None,
        typer.Option(
            "--mode",
            help="Project mode: new or existing. Skips the interactive prompt.",
        ),
    ] = None,
    task: Annotated[
        ProjectTask | None,
        typer.Option(
            "--task",
            help=(
                "Session task for existing projects: "
                "full_workflow, security_audit, bug_hunt, ui_redesign, "
                "specific_issue, or add_feature."
            ),
        ),
    ] = None,
    complexity: Annotated[
        TaskComplexity | None,
        typer.Option(
            "--complexity",
            help="Task complexity level: auto, level_1, level_2, or level_3.",
        ),
    ] = None,
    ide: Annotated[
        list[IdeKind] | None,
        typer.Option(
            "--ide",
            help="AI environment(s) to configure: codex, claude, antigravity, vscode, custom.",
        ),
    ] = None,
) -> None:
    """Safely initialize ADF in a new or existing project.

    For existing projects, ADF detects completed domains (frontend, backend,
    database, auth, CI) and writes an analysis scaffold that the IDE agent
    fills in during the existing_project_analysis stage.
    """

    try:
        result = initialize_project(
            path,
            initialize_git=initialize_git,
            mode_override=mode,
            task_override=task,
            complexity_override=complexity,
            ide_override=ide,
        )
    except InitializationError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    created = sum(item.status is FileStatus.CREATED for item in result.files)
    typer.echo(f"Initialized {result.inspection.root}")
    typer.echo(f"Project mode: {result.mode.value}")
    typer.echo(f"Session task: {result.task.value}")
    typer.echo(f"Completed domains: {result.inspection.domain_status.summary}")
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


@requirements_app.command("screenshots")
def sync_screenshots(
    path: Annotated[
        Path,
        typer.Option("--path", help="Project directory containing requirements/screenshots."),
    ] = Path("."),
) -> None:
    """Discover screenshot references and publish an immutable manifest revision."""

    try:
        result = ScreenshotManager(path).sync()
    except RequirementsError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    action = "Unchanged" if result.duplicate else "Published"
    typer.echo(f"{action} screenshot revision {result.revision}.")
    typer.echo(f"Screenshot files: {result.file_count}")
    typer.echo("Manifest: requirements/screenshots/manifest.json")
    typer.echo("Analysis: docs/ui-ux/screenshot-reference-analysis.md")


@app.command("analyze")
def analyze(
    path: Annotated[Path, typer.Option("--path")] = Path("."),
    focus: Annotated[
        str | None,
        typer.Option("--focus", help="Optional feature or change query for impact analysis."),
    ] = None,
) -> None:
    """Inspect project structure, dependencies, test runners, and optional change impact."""

    try:
        report = analyze_existing_project(path)
    except (OSError, NotADirectoryError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    inspection = report.inspection
    typer.echo(f"Project root: {inspection.root}")
    typer.echo(f"Empty: {'yes' if inspection.is_empty else 'no'}")
    typer.echo(f"Git root: {inspection.git_root or 'none'}")
    if report.git_branch:
        dirty_label = "dirty" if report.git_dirty else "clean"
        typer.echo(f"Git branch: {report.git_branch} ({dirty_label})")
    typer.echo(f"Technologies: {', '.join(inspection.technologies) or 'none detected'}")
    typer.echo(f"Package managers: {', '.join(inspection.package_managers) or 'none detected'}")
    typer.echo(f"Completed domains: {inspection.domain_status.summary}")
    typer.echo(f"Modules: {', '.join(report.modules) or 'none detected'}")
    typer.echo(f"Test runners: {', '.join(report.test_runners) or 'none detected'}")
    typer.echo(f"TODO/FIXME count: {report.todo_count}")
    if focus:
        impact = analyze_impact(path, focus)
        typer.echo(f"Impact query: {impact.query}")
        typer.echo(f"Affected domains: {', '.join(impact.affected_domains) or 'none detected'}")
        typer.echo(f"Matched files ({len(impact.matched_files)}):")
        for item in impact.matched_files:
            typer.echo(f"  - {item}")
        typer.echo(f"Related tests ({len(impact.related_tests)}):")
        for item in impact.related_tests:
            typer.echo(f"  - {item}")


@app.command("plan")
def plan(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """Display the dynamic workflow route and task complexity plan."""

    try:
        service = WorkflowService(path)
        current = service.status()
        route = service.workflow_route()
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Mode: {route['mode']}")
    typer.echo(f"Task: {route['task']}")
    typer.echo(f"Complexity: {route['complexity']}")
    typer.echo(f"Current stage: {current['current_stage']}")
    typer.echo("Planned stages:")
    for stage_id in route["stages"]:
        marker = "*" if stage_id == current["current_stage"] else "-"
        typer.echo(f"  {marker} {stage_id}")


@app.command("test")
def test_command(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """Show verification criteria and test readiness for the current stage."""

    try:
        service = WorkflowService(path)
        current = service.status()
        contract = service.stage_contract(current["current_stage"])
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Stage: {contract.id}")
    typer.echo(f"Execution: {current['execution']['status']}")
    typer.echo("Validation criteria:")
    for item in contract.validation_criteria:
        typer.echo(f"- {item}")
    typer.echo("Completion conditions:")
    for item in contract.completion_conditions:
        typer.echo(f"- {item}")


@app.command("docs")
def docs_command(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """List expected documentation deliverables and registered artifacts for the current stage."""

    try:
        service = WorkflowService(path)
        current = service.status()
        contract = service.stage_contract(current["current_stage"])
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Stage: {contract.id}")
    typer.echo("Expected outputs:")
    for output in contract.expected_outputs:
        typer.echo(f"- {output}")
    registered = current.get("artifacts", [])
    typer.echo(f"Registered artifacts: {len(registered)}")
    for artifact in registered:
        typer.echo(f"- {artifact['path']} (revision {artifact['revision']})")


@app.command("agents")
def agents_command(path: Annotated[Path, typer.Option("--path")] = Path(".")) -> None:
    """List specialized agents and their instruction files."""

    resolved = path.expanduser().resolve()
    registry_path = resolved / ".agentic" / "agent-registry.yaml"
    if not registry_path.is_file():
        typer.echo(f"Error: agent registry does not exist; run adt init: {registry_path}", err=True)
        raise typer.Exit(code=2)
    try:
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        typer.echo(f"Error: cannot read agent registry: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    for agent in data.get("agents", []):
        typer.echo(
            f"{agent['id']}: {agent['role']} ({agent.get('instructions_file', 'built-in')})"
        )


@app.command("providers")
def providers_command() -> None:
    """List supported AI provider adapters and their normalized capabilities."""

    for provider in list_providers():
        caps = provider.capabilities
        flags = [
            name
            for name, enabled in (
                ("skills", caps.supports_skills),
                ("rules", caps.supports_rules),
                ("slash_commands", caps.supports_slash_commands),
                ("subagents", caps.supports_subagents),
                ("commands", caps.supports_command_execution),
            )
            if enabled
        ]
        summary = ", ".join(flags) or "none"
        typer.echo(f"{provider.provider_id}: {provider.display_name} [{summary}]")


@app.command("design")
def design_command(
    instruction: Annotated[str, typer.Argument(help="Design change or iteration request.")],
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Record a context-aware design iteration request for Figma or frontend code."""

    if not instruction.strip():
        typer.echo("Error: design instruction cannot be blank", err=True)
        raise typer.Exit(code=2)
    resolved = path.expanduser().resolve()
    design_inputs = resolved / "docs" / "frontend" / "design-inputs.json"
    frontend_manifest = resolved / "docs" / "frontend" / "implementation-manifest.json"
    mode = "greenfield_frontend"
    if design_inputs.is_file():
        try:
            payload = json.loads(design_inputs.read_text(encoding="utf-8"))
            if "figma_mcp" in payload.get("methods", []):
                mode = "figma_and_frontend"
        except (OSError, json.JSONDecodeError):
            pass
    elif frontend_manifest.is_file():
        mode = "existing_frontend"

    session_file = resolved / ".agentic" / "state" / "design-session.json"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(
        json.dumps({"mode": mode, "instruction": instruction.strip()}, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        service = WorkflowService(resolved)
        current = service.status()
        if current["status"] == "active" and current["execution"]["status"] == "in_progress":
            service.set_current_task(f"design: {instruction.strip()}")
    except StateError:
        pass
    typer.echo(f"Design mode: {mode}")
    typer.echo(f"Recorded design instruction: {instruction.strip()}")
    typer.echo("Next: apply changes with ui_ux_designer / frontend_developer and verify visuals.")


@preferences_app.callback()
def preferences_default(
    context: typer.Context,
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Show effective merged design preferences when no subcommand is supplied."""

    if context.invoked_subcommand is not None:
        return
    try:
        prefs = resolve_effective_preferences(path)
    except ConfigurationError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(yaml.safe_dump(prefs.model_dump(mode="json"), sort_keys=False).rstrip())


@preferences_app.command("set")
def preferences_set(
    key: Annotated[str, typer.Argument(help="Preference field name (e.g. minimalism_level).")],
    value: Annotated[str, typer.Argument(help="Preference value (comma-separated for lists).")],
    scope: Annotated[
        str, typer.Option("--scope", help="Target scope: project or global.")
    ] = "project",
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Update a user (global) or project-specific design preference."""

    target = (
        default_global_preferences_path()
        if scope == "global"
        else project_preferences_path(path)
    )
    try:
        updated = update_preference_field(target, key, value)
    except ConfigurationError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Updated {scope} preference `{key}`.")
    typer.echo(f"{key}: {getattr(updated, key)}")


@preferences_app.command("reset")
def preferences_reset(
    scope: Annotated[
        str, typer.Option("--scope", help="Target scope: project or global.")
    ] = "project",
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Reset project or global design preferences to clean defaults."""

    target = (
        default_global_preferences_path()
        if scope == "global"
        else project_preferences_path(path)
    )
    reset_preferences_file(target)
    typer.echo(f"Reset {scope} design preferences to defaults.")


@memory_app.callback()
def memory_default(
    context: typer.Context,
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Show persisted project memory and decisions."""

    if context.invoked_subcommand is not None:
        return
    try:
        memory = load_project_memory(path)
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Decisions: {len(memory.decisions)}")
    for item in memory.decisions:
        typer.echo(f"- {item.id}: {item.title} (by {item.author_agent})")


@memory_app.command("decide")
def memory_decide(
    decision_id: Annotated[str, typer.Argument(help="Unique decision ID (e.g. ADR-001).")],
    title: Annotated[str, typer.Argument(help="Short decision title.")],
    rationale: Annotated[str, typer.Argument(help="Why this decision was made.")],
    agent: Annotated[str, typer.Option("--agent")] = "main_orchestrator",
    supersedes: Annotated[str | None, typer.Option("--supersedes")] = None,
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Record a persistent project decision without overwriting prior decisions."""

    try:
        decision = record_project_decision(
            path, decision_id, title, rationale, author_agent=agent, supersedes=supersedes
        )
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Recorded decision {decision.id}: {decision.title}")


@app.command("evaluate")
def evaluate_command(
    agent_id: Annotated[str, typer.Argument(help="Specialist agent ID.")],
    stage_id: Annotated[str, typer.Argument(help="Workflow stage ID.")],
    score: Annotated[
        list[str],
        typer.Option("--score", help="Criterion score as key=1..5 (repeatable)."),
    ],
    notes: Annotated[str, typer.Option("--notes")] = "",
    path: Annotated[Path, typer.Option("--path")] = Path("."),
) -> None:
    """Evaluate an agent's output against role-specific quality standards."""

    parsed: dict[str, int] = {}
    for entry in score:
        if "=" not in entry:
            typer.echo(f"Error: invalid --score format '{entry}'; expected key=value", err=True)
            raise typer.Exit(code=2)
        key, raw_val = entry.split("=", 1)
        try:
            parsed[key.strip()] = int(raw_val.strip())
        except ValueError as exc:
            typer.echo(f"Error: score for {key.strip()} must be an integer", err=True)
            raise typer.Exit(code=2) from exc
    try:
        record = evaluate_agent_output(path, agent_id, stage_id, parsed, notes=notes)
    except StateError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    typer.echo(f"Evaluated {record.agent_id} on {record.stage_id}: avg={record.average_score}")
    typer.echo(f"Needs improvement: {'yes' if record.needs_improvement else 'no'}")

