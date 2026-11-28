from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_framework.cli import app
from agentic_framework.core.evaluation import evaluate_agent_output
from agentic_framework.core.memory import (
    load_project_memory,
    record_agent_outcome,
    record_project_decision,
)
from agentic_framework.exceptions import StateError

runner = CliRunner()


def test_project_decisions_are_append_only_and_cannot_be_silently_overwritten(
    tmp_path: Path,
) -> None:
    d1 = record_project_decision(
        tmp_path,
        "ADR-001",
        "Use PostgreSQL",
        "Relational integrity for billing",
        author_agent="software_architect",
    )
    assert d1.id == "ADR-001"

    with pytest.raises(StateError, match="already exists"):
        record_project_decision(tmp_path, "ADR-001", "Overwrite", "Bad")

    d2 = record_project_decision(
        tmp_path,
        "ADR-002",
        "Use PostgreSQL with read replica",
        "Scale read queries",
        supersedes="ADR-001",
    )
    assert d2.supersedes == "ADR-001"
    memory = load_project_memory(tmp_path)
    assert len(memory.decisions) == 2

    note = record_agent_outcome(
        tmp_path,
        "backend_developer",
        "implementation",
        "completed",
        "Implemented billing API",
        limitations=("Rate limiter uses in-memory store",),
    )
    assert note.agent_id == "backend_developer"


def test_agent_evaluation_checks_role_criteria_and_flags_weak_output(tmp_path: Path) -> None:
    with pytest.raises(StateError, match="missing evaluation criteria"):
        evaluate_agent_output(tmp_path, "qa_engineer", "qa_and_testing", {"test_coverage": 4})

    weak = evaluate_agent_output(
        tmp_path,
        "qa_engineer",
        "qa_and_testing",
        {
            "test_coverage": 2,
            "edge_case_identification": 4,
            "bug_detection": 4,
            "test_reliability": 4,
        },
        notes="Missed negative boundary cases",
    )
    assert weak.needs_improvement is True
    assert weak.average_score == 3.5

    res = runner.invoke(
        app,
        [
            "evaluate",
            "qa_engineer",
            "qa_and_testing",
            "--score",
            "test_coverage=5",
            "--score",
            "edge_case_identification=4",
            "--score",
            "bug_detection=5",
            "--score",
            "test_reliability=4",
            "--path",
            str(tmp_path),
        ],
    )
    assert res.exit_code == 0
    assert "Needs improvement: no" in res.stdout

    dec_res = runner.invoke(
        app,
        ["memory", "decide", "ADR-003", "Use JWT", "Stateless auth", "--path", str(tmp_path)],
    )
    assert dec_res.exit_code == 0
    show_res = runner.invoke(app, ["memory", "--path", str(tmp_path)])
    assert show_res.exit_code == 0
    assert "ADR-003: Use JWT" in show_res.stdout
