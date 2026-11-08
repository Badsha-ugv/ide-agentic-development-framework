"""Safe, deterministic project initialization."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from agentic_framework.adapters import generated_project_files
from agentic_framework.core.config import (
    FrameworkConfig,
    ProjectConfig,
    ProjectMode,
    ProjectTask,
    dump_config,
    load_config,
)
from agentic_framework.core.project import ProjectInspection, inspect_project
from agentic_framework.exceptions import ConfigurationError, InitializationError
from agentic_framework.state import RuntimeStore

_DIRECTORIES = (
    ".agentic/database",
    ".agentic/state",
    ".agentic/checkpoints",
    ".agentic/logs",
    ".agentic/reports",
    ".agentic/proposals",
    ".agents/rules",
    ".agents/skills",
    ".codex/agents",
    ".github/agents",
    ".github/instructions",
    ".github/workflows",
    "requirements/inbox",
    "requirements/screenshots/desktop/homepage",
    "requirements/screenshots/desktop/dashboard",
    "requirements/screenshots/desktop/other",
    "requirements/screenshots/mobile/homepage",
    "requirements/screenshots/mobile/dashboard",
    "requirements/screenshots/mobile/other",
    "requirements/screenshots/admin-dashboard",
    "requirements/screenshots/vendor-dashboard",
    "requirements/screenshots/customer-dashboard",
    "requirements/screenshots/references",
    "requirements/versions",
    "requirements/reports",
    "docs/discovery",
    "docs/requirements",
    "docs/architecture",
    "docs/design",
    "docs/ui-ux",
    "docs/frontend",
    "docs/backend",
    "docs/decisions",
    "docs/planning",
    "docs/technical",
    "docs/revisions",
    "docs/reports",
    "tests",
)

_AGENTS = """# Project agent instructions

This project uses the Agentic Development Framework (ADF).

- Read `.agentic/config.yaml` before framework operations.
- Preserve existing project files and unrelated working-tree changes.
- Do not expose secrets or perform destructive operations without explicit approval.
- Antigravity workspace skills register `/start`, `/status`, `/pause`, `/continue`, `/stop`,
  `/review`, `/approve`, `/revise`, `/requirements`, `/tasks`, `/adf-resume`, and `/adf`.
- Use the shared `agentic-commands` skill for the complete execution protocol.
- For `/start`, `/continue`, and `/adf-resume`, execute the current stage contract: inspect inputs,
  reason about the requested work, create deliverables, register them with `adt artifact register`,
  and run `adt stage complete`. The CLI persists state; the IDE agent performs the work.
- Never treat successful `adt continue` output as completion or stage advancement.
- Do not claim a task or phase is complete until its required checks pass.
- Build the complete production frontend before backend work: verify its environment, inspect actual
  Figma/screenshots, browser-test all pages and viewports, and wait for explicit frontend approval.
- Design quality is a primary deliverable: establish a full design system (colors, typography,
  spacing, motion) before writing any page code. Research comparable production websites to
  understand industry design conventions relevant to this project.
- Keep frontend and backend separate until the API integration stage.
- Never create a disposable prototype or silently simplify an approved visual reference.
- For existing projects, read the existing-project-analysis before proposing any work.
"""

_REQUIREMENTS_README = """# Project requirements

Place source requirement files in `inbox/`, then run `adt requirements ingest`. ADF copies every
source byte-for-byte into an immutable directory under `versions/`, detects duplicates using
SHA-256 hashes, and compares each new version with its predecessor. Files in `inbox/` are never
silently overwritten or removed.

Place PNG, JPG, JPEG, or WEBP visual references anywhere under `screenshots/`. ADF discovers them
recursively, preserves immutable revisions, and updates the screenshot manifest with
`adt requirements screenshots`. Folder names provide context but never replace visual inspection.
"""

_GITIGNORE = """# Agentic Development Framework local runtime data
.agentic/database/
.agentic/state/
.agentic/checkpoints/
.agentic/logs/
.agentic/proposals/
"""

_TASK_LABELS: dict[ProjectTask, str] = {
    ProjectTask.FULL_WORKFLOW: "Full workflow (requirements → frontend → backend → testing)",
    ProjectTask.SECURITY_AUDIT: "Security audit (analyze existing code for vulnerabilities)",
    ProjectTask.BUG_HUNT: "Bug hunt (find and fix defects in existing code)",
    ProjectTask.UI_REDESIGN: "UI redesign (rebuild the frontend with improved design)",
    ProjectTask.SPECIFIC_ISSUE: "Specific issue (address a targeted known problem)",
    ProjectTask.ADD_FEATURE: "Add feature (extend existing functionality)",
}


class FileStatus(StrEnum):
    """Outcome of safely installing one generated file."""

    CREATED = "created"
    UNCHANGED = "unchanged"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class FileResult:
    """Outcome and optional proposal for one generated file."""

    path: Path
    status: FileStatus
    proposal: Path | None = None


@dataclass(slots=True)
class InitializationResult:
    """Complete result returned to CLI and tests."""

    inspection: ProjectInspection
    mode: ProjectMode
    task: ProjectTask = ProjectTask.FULL_WORKFLOW
    files: list[FileResult] = field(default_factory=list)
    git_initialized: bool = False

    @property
    def conflicts(self) -> tuple[FileResult, ...]:
        return tuple(item for item in self.files if item.status is FileStatus.CONFLICT)


def _proposal_path(root: Path, relative: Path) -> Path:
    proposal_root = root / ".agentic" / "proposals"
    return proposal_root / relative.parent / f"{relative.name}.proposed"


def _safe_install(root: Path, relative: str, content: str) -> FileResult:
    relative_path = Path(relative)
    destination = root / relative_path
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
        return FileResult(path=relative_path, status=FileStatus.CREATED)

    try:
        existing = destination.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InitializationError(f"cannot compare existing file {destination}: {exc}") from exc
    if existing == content:
        return FileResult(path=relative_path, status=FileStatus.UNCHANGED)

    proposal = _proposal_path(root, relative_path)
    proposal.parent.mkdir(parents=True, exist_ok=True)
    if not proposal.exists() or proposal.read_text(encoding="utf-8") != content:
        proposal.write_text(content, encoding="utf-8")
    return FileResult(
        path=relative_path,
        status=FileStatus.CONFLICT,
        proposal=proposal.relative_to(root),
    )


def _configuration(
    root: Path,
    inspection: ProjectInspection,
    *,
    mode_override: ProjectMode | None = None,
    task_override: ProjectTask | None = None,
) -> tuple[FrameworkConfig, bool]:
    existing = root / ".agentic" / "config.yaml"
    if existing.is_file():
        try:
            config = load_config(existing)
            # Apply overrides if provided on top of the existing config.
            if mode_override is not None or task_override is not None:
                new_mode = mode_override if mode_override is not None else config.project.mode
                new_task = task_override if task_override is not None else config.project.task
                config = config.model_copy(
                    update={"project": config.project.model_copy(
                        update={"mode": new_mode, "task": new_task}
                    )}
                )
            return config, True
        except ConfigurationError:
            pass

    if mode_override is not None:
        mode = mode_override
    elif inspection.is_empty:
        mode = ProjectMode.NEW
    else:
        mode = ProjectMode.EXISTING

    task = task_override if task_override is not None else ProjectTask.FULL_WORKFLOW
    return (
        FrameworkConfig(project=ProjectConfig(name=root.name, mode=mode, task=task)),
        False,
    )


def _run_git_init(root: Path) -> None:
    try:
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise InitializationError("Git is not installed or is not available on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or "unknown Git error"
        raise InitializationError(f"Git initialization failed: {detail}") from exc


def _existing_project_analysis_report(
    inspection: ProjectInspection,
    task: ProjectTask,
) -> str:
    """Generate a structured analysis report for existing projects."""
    domain = inspection.domain_status
    technologies = ", ".join(inspection.technologies) or "none detected"
    managers = ", ".join(inspection.package_managers) or "none detected"
    task_label = _TASK_LABELS.get(task, task.value)

    domain_rows = [
        f"| Frontend     | {'✅ detected' if domain.frontend else '❌ not detected'} |",
        f"| Backend      | {'✅ detected' if domain.backend else '❌ not detected'} |",
        f"| Database     | {'✅ detected' if domain.database else '❌ not detected'} |",
        f"| Auth         | {'✅ detected' if domain.auth else '❌ not detected'} |",
        f"| CI/CD        | {'✅ detected' if domain.ci else '❌ not detected'} |",
    ]

    return "\n".join([
        "# Existing project analysis",
        "",
        "This report is generated automatically during `adt init` for existing projects.",
        "The IDE agent must replace the placeholder sections below with actual findings.",
        "",
        "## Project snapshot",
        "",
        f"- **Technologies detected**: {technologies}",
        f"- **Package managers**: {managers}",
        f"- **Session task**: {task_label}",
        "",
        "## Domain completion (filesystem detection)",
        "",
        "| Domain       | Status |",
        "|--------------|--------|",
        *domain_rows,
        "",
        "> **Important**: These are coarse filesystem heuristics. The IDE agent must verify "
        "each domain by reading the actual source files and confirming functionality.",
        "",
        "## Required agent analysis",
        "",
        "The `existing_project_analysis` stage contract requires the IDE agent to:",
        "",
        "1. Walk the full source tree and catalogue every significant file.",
        "2. Assess each domain with file-level evidence (not just marker detection).",
        "3. Identify issues relevant to the session task.",
        "4. Record all findings in `docs/discovery/existing-project-analysis.md` and "
        "`docs/discovery/work-completion-status.md`.",
        "",
        "## Session task guidance",
        "",
        f"**Selected task**: `{task.value}`",
        "",
        {
            ProjectTask.FULL_WORKFLOW: (
                "Run the full ADF workflow. If some domains are already complete, "
                "the agent should validate them rather than rebuilding from scratch."
            ),
            ProjectTask.SECURITY_AUDIT: (
                "Focus the analysis on security: authentication, authorization, "
                "input validation, secrets management, dependency CVEs, and injection risks. "
                "Advance directly to the security_testing stage after analysis."
            ),
            ProjectTask.BUG_HUNT: (
                "Focus the analysis on defect identification: failing tests, error logs, "
                "broken routes, type errors, and inconsistent behavior. "
                "Prioritize reproducing and fixing reported issues."
            ),
            ProjectTask.UI_REDESIGN: (
                "Focus the analysis on the existing frontend: current pages, design system "
                "(or lack thereof), component structure, and design gaps. "
                "The frontend_implementation stage will rebuild with an improved design."
            ),
            ProjectTask.SPECIFIC_ISSUE: (
                "Focus the analysis on the specific issue provided by the user. "
                "Understand the context, reproduce the issue, and plan the fix."
            ),
            ProjectTask.ADD_FEATURE: (
                "Focus the analysis on the existing architecture and code conventions. "
                "Understand the established patterns before adding new functionality."
            ),
        }.get(task, "Follow the standard ADF workflow for the selected task."),
        "",
    ]) + "\n"


def _report(result: InitializationResult) -> str:
    inspection = result.inspection
    technologies = ", ".join(inspection.technologies) or "none detected"
    managers = ", ".join(inspection.package_managers) or "none detected"
    if result.git_initialized:
        git_state = "initialized"
    elif inspection.has_git:
        git_state = "detected"
    else:
        git_state = "skipped"
    lines = [
        "# ADF initialization report",
        "",
        f"- Project root: `{inspection.root}`",
        f"- Project mode: `{result.mode.value}`",
        f"- Session task: `{result.task.value}`",
        f"- Git: {git_state}",
        f"- Technologies: {technologies}",
        f"- Package managers: {managers}",
        f"- Completed domains: {inspection.domain_status.summary}",
        f"- Conflicts: {len(result.conflicts)}",
    ]
    if result.conflicts:
        lines.extend(["", "## Conflicts", ""])
        lines.extend(
            f"- `{item.path}` preserved; proposed content written to `{item.proposal}`"
            for item in result.conflicts
        )
    return "\n".join(lines) + "\n"


def initialize_project(
    target: Path,
    *,
    initialize_git: bool = True,
    git_initializer: Callable[[Path], None] = _run_git_init,
    mode_override: ProjectMode | None = None,
    task_override: ProjectTask | None = None,
) -> InitializationResult:
    """Initialize a target without overwriting existing project files.

    Parameters
    ----------
    target:
        The project directory to initialize.
    initialize_git:
        When True, run ``git init`` if no repository is detected.
    git_initializer:
        Replacement for the default ``git init`` subprocess call (used in tests).
    mode_override:
        Explicitly set the project mode instead of auto-detecting.
    task_override:
        Explicitly set the session task.
    """

    try:
        inspection = inspect_project(target)
    except (OSError, NotADirectoryError) as exc:
        raise InitializationError(str(exc)) from exc

    root = inspection.root
    root.mkdir(parents=True, exist_ok=True)
    config, existing_config_is_valid = _configuration(
        root, inspection, mode_override=mode_override, task_override=task_override
    )
    result = InitializationResult(
        inspection=inspection, mode=config.project.mode, task=config.project.task
    )

    for relative in _DIRECTORIES:
        (root / relative).mkdir(parents=True, exist_ok=True)

    if existing_config_is_valid:
        result.files.append(
            FileResult(path=Path(".agentic/config.yaml"), status=FileStatus.UNCHANGED)
        )
    else:
        result.files.append(_safe_install(root, ".agentic/config.yaml", dump_config(config)))

    generated = {
        ".gitignore": _GITIGNORE,
        "AGENTS.md": _AGENTS,
        "requirements/README.md": _REQUIREMENTS_README,
    }
    generated.update(generated_project_files())
    result.files.extend(_safe_install(root, path, content) for path, content in generated.items())

    if initialize_git and not inspection.has_git:
        git_initializer(root)
        result.git_initialized = True

    store = RuntimeStore(root)
    store.initialize()

    report_path = root / ".agentic" / "reports" / "initialization.md"
    report_path.write_text(_report(result), encoding="utf-8")

    # For existing projects, write the analysis scaffold.
    if result.mode is ProjectMode.EXISTING:
        analysis_path = root / ".agentic" / "reports" / "existing-project-analysis.md"
        analysis_path.write_text(
            _existing_project_analysis_report(inspection, result.task), encoding="utf-8"
        )

    workflow = store.workflow()
    if workflow["current_stage"] == "project_initialization":
        store.register_artifact("project_initialization", ".agentic/reports/initialization.md")
        store.update_execution("project_initialization", "completed")

        # For existing projects with specific tasks, skip discovery stages that
        # apply only to new greenfield work.
        if result.mode is ProjectMode.EXISTING:
            next_stage = "existing_project_analysis"
        else:
            next_stage = "project_discovery"

        store.update_workflow("not_started", next_stage)
        store.create_checkpoint("project_initialized")
    return result
