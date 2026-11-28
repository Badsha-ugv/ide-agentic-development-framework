"""Persistent, versioned project and agent memory independent of chat history."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import Field

from agentic_framework.core.config import StrictModel
from agentic_framework.exceptions import StateError


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ProjectDecision(StrictModel):
    """An append-only architectural or product decision."""

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    author_agent: str = Field(min_length=1)
    supersedes: str | None = None
    created_at: str


class ProjectMemory(StrictModel):
    """Durable project-level memory stored under .agentic/memory/project-memory.json."""

    schema_version: int = Field(default=1, ge=1, le=1)
    description: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    architecture_summary: str = ""
    coding_conventions: list[str] = Field(default_factory=list)
    decisions: list[ProjectDecision] = Field(default_factory=list)


class AgentExecutionNote(StrictModel):
    """Recorded outcome and limitations for an agent execution."""

    agent_id: str
    stage_id: str
    status: str
    summary: str
    limitations: list[str] = Field(default_factory=list)
    recorded_at: str


def _memory_dir(root: Path) -> Path:
    return root.expanduser().resolve() / ".agentic" / "memory"


def load_project_memory(root: Path) -> ProjectMemory:
    """Load persisted project memory or return an empty baseline."""

    path = _memory_dir(root) / "project-memory.json"
    if not path.is_file():
        return ProjectMemory()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateError(f"invalid project memory file: {exc}") from exc
    return ProjectMemory.model_validate(data)


def save_project_memory(root: Path, memory: ProjectMemory) -> Path:
    """Persist validated project memory atomically."""

    path = _memory_dir(root) / "project-memory.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(memory.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    return path


def record_project_decision(
    root: Path,
    decision_id: str,
    title: str,
    rationale: str,
    author_agent: str = "main_orchestrator",
    *,
    supersedes: str | None = None,
) -> ProjectDecision:
    """Append a new project decision without silently overwriting existing ones."""

    memory = load_project_memory(root)
    existing_ids = {item.id for item in memory.decisions}
    if decision_id in existing_ids:
        raise StateError(
            f"decision {decision_id} already exists; use a new ID with supersedes="
        )
    if supersedes is not None and supersedes not in existing_ids:
        raise StateError(f"superseded decision does not exist: {supersedes}")
    decision = ProjectDecision(
        id=decision_id.strip(),
        title=title.strip(),
        rationale=rationale.strip(),
        author_agent=author_agent.strip(),
        supersedes=supersedes,
        created_at=_now(),
    )
    memory.decisions.append(decision)
    save_project_memory(root, memory)
    return decision


def record_agent_outcome(
    root: Path,
    agent_id: str,
    stage_id: str,
    status: str,
    summary: str,
    limitations: tuple[str, ...] | list[str] = (),
) -> AgentExecutionNote:
    """Append an agent execution note to .agentic/memory/agent-memory.json."""

    path = _memory_dir(root) / "agent-memory.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                items = loaded
        except (OSError, json.JSONDecodeError) as exc:
            raise StateError(f"invalid agent memory file: {exc}") from exc
    note = AgentExecutionNote(
        agent_id=agent_id,
        stage_id=stage_id,
        status=status,
        summary=summary.strip(),
        limitations=list(limitations),
        recorded_at=_now(),
    )
    items.append(note.model_dump(mode="json"))
    path.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")
    return note
