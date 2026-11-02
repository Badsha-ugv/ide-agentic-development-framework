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
    "requirements/versions",
    "requirements/reports",
    "docs/discovery",
    "docs/requirements",
    "docs/architecture",
    "docs/design",
    "docs/decisions",
    "docs/planning",
    "docs/technical",
    "docs/revisions",
    "docs/reports",
    "design-prototype",
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
"""

_REQUIREMENTS_README = """# Project requirements

Place source requirement files in `inbox/`, then run `adt requirements ingest`. ADF copies every
source byte-for-byte into an immutable directory under `versions/`, detects duplicates using
SHA-256 hashes, and compares each new version with its predecessor. Files in `inbox/` are never
silently overwritten or removed.
"""

_GITIGNORE = """# Agentic Development Framework local runtime data
.agentic/database/
.agentic/state/
.agentic/checkpoints/
.agentic/logs/
.agentic/proposals/
"""


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


def _configuration(root: Path, inspection: ProjectInspection) -> tuple[FrameworkConfig, bool]:
    existing = root / ".agentic" / "config.yaml"
    if existing.is_file():
        try:
            return load_config(existing), True
        except ConfigurationError:
            pass
    mode = ProjectMode.NEW if inspection.is_empty else ProjectMode.EXISTING
    return FrameworkConfig(project=ProjectConfig(name=root.name, mode=mode)), False


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
        f"- Git: {git_state}",
        f"- Technologies: {technologies}",
        f"- Package managers: {managers}",
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
) -> InitializationResult:
    """Initialize a target without overwriting existing project files."""

    try:
        inspection = inspect_project(target)
    except (OSError, NotADirectoryError) as exc:
        raise InitializationError(str(exc)) from exc

    root = inspection.root
    root.mkdir(parents=True, exist_ok=True)
    config, existing_config_is_valid = _configuration(root, inspection)
    result = InitializationResult(inspection=inspection, mode=config.project.mode)

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
    workflow = store.workflow()
    if workflow["current_stage"] == "project_initialization":
        store.register_artifact("project_initialization", ".agentic/reports/initialization.md")
        store.update_execution("project_initialization", "completed")
        store.update_workflow("not_started", "project_discovery")
        store.create_checkpoint("project_initialized")
    return result
