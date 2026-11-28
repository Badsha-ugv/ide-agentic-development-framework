from pathlib import Path

import pytest

from agentic_framework.core.config import ProjectMode, ProjectTask, TaskComplexity
from agentic_framework.core.initialization import initialize_project
from agentic_framework.core.workflow import WorkflowService
from agentic_framework.exceptions import StateError


def test_existing_security_audit_advances_along_dynamic_route(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    initialize_project(
        tmp_path,
        initialize_git=False,
        mode_override=ProjectMode.EXISTING,
        task_override=ProjectTask.SECURITY_AUDIT,
    )
    service = WorkflowService(tmp_path)
    service.start()

    assert service.status()["current_stage"] == "existing_project_analysis"
    for relative in service.stage_contract().expected_outputs:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Analysis\n\nVerified.\n", encoding="utf-8")
        service.register_artifact(relative)

    advanced = service.complete_stage()
    assert advanced["current_stage"] == "security_testing"


def test_task_dependencies_enforce_execution_order(tmp_path: Path) -> None:
    initialize_project(
        tmp_path,
        initialize_git=False,
        mode_override=ProjectMode.NEW,
        complexity_override=TaskComplexity.LEVEL_2,
    )
    service = WorkflowService(tmp_path)
    service.create_task("T-1", "requirements_analyst", "Clarify scope", "Define scope")
    service.create_task(
        "T-2",
        "backend_developer",
        "Build API",
        "Implement endpoint",
        dependencies=("T-1",),
    )

    with pytest.raises(StateError, match="blocked by incomplete dependencies: T-1"):
        service.start_task("T-2")

    service.start_task("T-1")
    service.complete_task("T-1")
    started = service.start_task("T-2")
    assert started["status"] == "in_progress"
    completed = service.complete_task("T-2")
    assert completed["status"] == "completed"
