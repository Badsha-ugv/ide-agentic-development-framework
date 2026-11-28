import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_framework.cli import app
from agentic_framework.core.config import ProjectMode, ProjectTask, TaskComplexity
from agentic_framework.core.evaluation import evaluate_agent_output
from agentic_framework.core.gates import validate_security_findings_gate
from agentic_framework.core.initialization import initialize_project
from agentic_framework.core.intelligence import analyze_existing_project, analyze_impact
from agentic_framework.core.memory import (
    load_project_memory,
    record_agent_outcome,
    record_project_decision,
)
from agentic_framework.core.mobile import validate_mobile_evidence
from agentic_framework.core.preferences import load_preferences_file, project_preferences_path
from agentic_framework.core.routing import resolve_workflow_route
from agentic_framework.core.workflow import WorkflowService
from agentic_framework.exceptions import ConfigurationError, StateError
from agentic_framework.integrations.git import create_task_branch, inspect_git_state, safe_commit

runner = CliRunner()


def test_routing_covers_all_modes_and_tasks() -> None:
    assert resolve_workflow_route(
        ProjectMode.NEW, ProjectTask.SPECIFIC_ISSUE, TaskComplexity.LEVEL_1
    )[0] == "project_discovery"
    assert "frontend_implementation" in resolve_workflow_route(
        ProjectMode.EXISTING, ProjectTask.UI_REDESIGN, TaskComplexity.AUTO
    )
    assert "implementation" in resolve_workflow_route(
        ProjectMode.EXISTING, ProjectTask.ADD_FEATURE, TaskComplexity.LEVEL_1
    )
    assert "requirements_analysis" in resolve_workflow_route(
        ProjectMode.EXISTING, ProjectTask.ADD_FEATURE, TaskComplexity.LEVEL_2
    )
    assert "project_discovery" in resolve_workflow_route(
        ProjectMode.EXISTING, ProjectTask.ADD_FEATURE, TaskComplexity.LEVEL_3
    )
    assert "project_discovery" in resolve_workflow_route(
        ProjectMode.EXISTING, ProjectTask.FULL_WORKFLOW, TaskComplexity.AUTO
    )
    assert "development_planning" in resolve_workflow_route(
        ProjectMode.EXISTING, ProjectTask.BUG_HUNT, TaskComplexity.LEVEL_2
    )
    assert resolve_workflow_route(ProjectMode.AUTO, ProjectTask.FULL_WORKFLOW)[0] == (
        "project_initialization"
    )


def test_mobile_validation_error_branches(tmp_path: Path) -> None:
    mobile_docs = tmp_path / "docs" / "mobile"
    mobile_docs.mkdir(parents=True)
    (mobile_docs / "implementation-manifest.json").write_text("[]", encoding="utf-8")
    with pytest.raises(StateError, match="JSON object"):
        validate_mobile_evidence(tmp_path)

    (mobile_docs / "implementation-manifest.json").write_text(
        json.dumps({"framework": "unknown", "platforms": ["android", "ios"]}), encoding="utf-8"
    )
    with pytest.raises(StateError, match="supported framework"):
        validate_mobile_evidence(tmp_path)

    (mobile_docs / "implementation-manifest.json").write_text(
        json.dumps({"framework": "flutter", "platforms": ["android"]}), encoding="utf-8"
    )
    with pytest.raises(StateError, match="both android and ios"):
        validate_mobile_evidence(tmp_path)

    (mobile_docs / "implementation-manifest.json").write_text(
        json.dumps({"framework": "flutter", "platforms": ["android", "ios"]}), encoding="utf-8"
    )
    (mobile_docs / "device-verification.json").write_text(
        json.dumps({"passed": False}), encoding="utf-8"
    )
    with pytest.raises(StateError, match="has not passed"):
        validate_mobile_evidence(tmp_path)


def test_intelligence_requirements_txt_git_and_domains(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    (tmp_path / "requirements.txt").write_text("# comment\nflask>=3.0\n", encoding="utf-8")
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "auth_routes.py").write_text("def login(): pass\n", encoding="utf-8")
    (tmp_path / "db").mkdir()
    (tmp_path / "db" / "auth_migration.py").write_text("# auth migration\n", encoding="utf-8")

    report = analyze_existing_project(tmp_path)
    assert "flask" in report.dependencies["python"]
    assert report.git_dirty is True

    impact = analyze_impact(tmp_path, "fix auth login")
    assert "backend" in impact.affected_domains
    assert "auth" in impact.affected_domains
    assert "database" in impact.affected_domains


def test_git_and_gates_error_branches(tmp_path: Path) -> None:
    assert inspect_git_state(tmp_path).is_repo is False
    with pytest.raises(StateError, match="outside a Git repository"):
        create_task_branch(tmp_path, "feat/x")
    with pytest.raises(StateError, match="invalid Git branch"):
        create_task_branch(tmp_path, "bad..branch")
    with pytest.raises(StateError, match="blank"):
        safe_commit(tmp_path, "  ", ["a.py"])
    with pytest.raises(StateError, match="one or more paths"):
        safe_commit(tmp_path, "msg", [])
    with pytest.raises(StateError, match="outside a Git repository"):
        safe_commit(tmp_path, "msg", ["a.py"])

    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    (tmp_path / "dirty.txt").write_text("x", encoding="utf-8")
    with pytest.raises(StateError, match="uncommitted changes"):
        create_task_branch(tmp_path, "feat/clean")

    reports = tmp_path / "docs" / "reports"
    reports.mkdir(parents=True)
    (reports / "security-findings.json").write_text("{bad", encoding="utf-8")
    with pytest.raises(StateError, match="invalid security findings"):
        validate_security_findings_gate(tmp_path)
    (reports / "security-findings.json").write_text("{}", encoding="utf-8")
    with pytest.raises(StateError, match="findings"):
        validate_security_findings_gate(tmp_path)


def test_memory_evaluation_preferences_and_cli_errors(tmp_path: Path) -> None:
    with pytest.raises(StateError, match="does not exist"):
        record_project_decision(tmp_path, "ADR-1", "T", "R", supersedes="ADR-0")

    mem_file = tmp_path / ".agentic" / "memory" / "project-memory.json"
    mem_file.parent.mkdir(parents=True)
    mem_file.write_text("{bad", encoding="utf-8")
    with pytest.raises(StateError, match="invalid project memory"):
        load_project_memory(tmp_path)

    agent_file = tmp_path / ".agentic" / "memory" / "agent-memory.json"
    agent_file.write_text("{bad", encoding="utf-8")
    with pytest.raises(StateError, match="invalid agent memory"):
        record_agent_outcome(tmp_path, "qa", "qa_and_testing", "ok", "done")

    with pytest.raises(StateError, match="between 1 and 5"):
        evaluate_agent_output(
            tmp_path,
            "qa_engineer",
            "qa_and_testing",
            {
                "test_coverage": 6,
                "edge_case_identification": 4,
                "bug_detection": 4,
                "test_reliability": 4,
            },
        )

    pref_path = project_preferences_path(tmp_path)
    pref_path.parent.mkdir(parents=True, exist_ok=True)
    pref_path.write_text("- not-a-mapping\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="YAML mapping"):
        load_preferences_file(pref_path)

    # CLI error branches on uninitialized directory
    empty = tmp_path / "empty"
    empty.mkdir()
    assert runner.invoke(app, ["plan", "--path", str(empty)]).exit_code == 2
    assert runner.invoke(app, ["test", "--path", str(empty)]).exit_code == 2
    assert runner.invoke(app, ["docs", "--path", str(empty)]).exit_code == 2
    assert runner.invoke(app, ["agents", "--path", str(empty)]).exit_code == 2
    assert runner.invoke(app, ["design", "   ", "--path", str(empty)]).exit_code == 2
    assert runner.invoke(app, ["evaluate", "qa", "s", "--score", "bad"]).exit_code == 2
    assert runner.invoke(app, ["evaluate", "qa", "s", "--score", "k=abc"]).exit_code == 2

    # Balanced approval policy on initialized project
    proj = tmp_path / "proj"
    initialize_project(proj, initialize_git=False)
    cfg = proj / ".agentic" / "config.yaml"
    cfg.write_text(
        cfg.read_text(encoding="utf-8").replace(
            "approval_policy: strict", "approval_policy: balanced"
        ),
        encoding="utf-8",
    )
    svc = WorkflowService(proj)
    assert svc._requires_manual_approval("frontend_review") is True
    assert svc._requires_manual_approval("requirements_review") is False
    assert svc._requires_manual_approval("project_discovery") is False

    # Task error branches
    with pytest.raises(StateError, match="cannot be blank"):
        svc.create_task(" ", "qa", " ", "desc")
    with pytest.raises(StateError, match="does not exist"):
        svc.create_task("T-1", "qa", "Title", "desc", dependencies=("MISSING",))
    svc.create_task("T-1", "qa", "Title", "desc")
    with pytest.raises(StateError, match="already exists"):
        svc.create_task("T-1", "qa", "Title", "desc")
    with pytest.raises(StateError, match="unknown task"):
        svc.start_task("NOPE")
    with pytest.raises(StateError, match="unknown task"):
        svc.complete_task("NOPE")
    svc.start_task("T-1")
    svc.complete_task("T-1")
    with pytest.raises(StateError, match="already completed"):
        svc.start_task("T-1")

    # Design figma_mcp + preferences reset CLI
    (proj / "docs" / "frontend").mkdir(parents=True, exist_ok=True)
    (proj / "docs" / "frontend" / "design-inputs.json").write_text(
        json.dumps({"methods": ["figma_mcp"]}), encoding="utf-8"
    )
    assert "figma_and_frontend" in runner.invoke(
        app, ["design", "align header", "--path", str(proj)]
    ).stdout
    assert runner.invoke(app, ["preferences", "reset", "--path", str(proj)]).exit_code == 0
