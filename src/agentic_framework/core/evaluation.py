"""Role-specific agent output evaluation without automatic self-rewriting."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import Field

from agentic_framework.core.config import StrictModel
from agentic_framework.exceptions import StateError

ROLE_CRITERIA: dict[str, tuple[str, ...]] = {
    "frontend_developer": (
        "design_accuracy",
        "code_quality",
        "accessibility",
        "responsiveness",
        "performance",
    ),
    "backend_developer": (
        "api_correctness",
        "database_integrity",
        "security",
        "maintainability",
        "performance",
    ),
    "qa_engineer": (
        "test_coverage",
        "edge_case_identification",
        "bug_detection",
        "test_reliability",
    ),
    "ui_ux_designer": (
        "usability",
        "visual_consistency",
        "design_simplicity",
        "human_centered_design",
        "reference_alignment",
    ),
}
_DEFAULT_CRITERIA: tuple[str, ...] = ("correctness", "completeness", "adherence_to_contract")


class AgentEvaluationRecord(StrictModel):
    """Persisted evaluation of one agent execution against role standards."""

    agent_id: str
    stage_id: str
    scores: dict[str, int]
    average_score: float = Field(ge=1.0, le=5.0)
    needs_improvement: bool
    notes: str = ""
    evaluated_at: str


def criteria_for_agent(agent_id: str) -> tuple[str, ...]:
    """Return role-specific evaluation criteria for an agent."""

    return ROLE_CRITERIA.get(agent_id, _DEFAULT_CRITERIA)


def evaluate_agent_output(
    root: Path,
    agent_id: str,
    stage_id: str,
    scores: dict[str, int],
    notes: str = "",
) -> AgentEvaluationRecord:
    """Validate role-specific scores (1..5), flag weak outputs, and persist history."""

    expected = criteria_for_agent(agent_id)
    missing = [criterion for criterion in expected if criterion not in scores]
    if missing:
        raise StateError(
            f"missing evaluation criteria for {agent_id}: {', '.join(missing)}"
        )
    for key, value in scores.items():
        if not isinstance(value, int) or value < 1 or value > 5:
            raise StateError(f"evaluation score for {key} must be an integer between 1 and 5")

    relevant_scores = {k: scores[k] for k in expected}
    avg = round(sum(relevant_scores.values()) / len(relevant_scores), 2)
    needs_improvement = avg < 3.5 or any(v < 3 for v in relevant_scores.values())

    record = AgentEvaluationRecord(
        agent_id=agent_id,
        stage_id=stage_id,
        scores=relevant_scores,
        average_score=avg,
        needs_improvement=needs_improvement,
        notes=notes.strip(),
        evaluated_at=datetime.now(UTC).isoformat(),
    )

    path = root.expanduser().resolve() / ".agentic" / "memory" / "evaluations.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, Any]] = []
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                history = loaded
        except (OSError, json.JSONDecodeError) as exc:
            raise StateError(f"invalid evaluations history file: {exc}") from exc
    history.append(record.model_dump(mode="json"))
    path.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")
    return record
