import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from agentic_framework.core.initialization import initialize_project
from agentic_framework.core.workflow import WorkflowService
from agentic_framework.exceptions import StateError


def test_pause_close_reopen_and_resume_from_checkpoint(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    service = WorkflowService(tmp_path)
    assert service.start()["status"] == "active"
    assert service.continue_workflow()["current_stage"] == "project_discovery"
    paused = service.pause()
    assert paused["status"] == "paused"

    with closing(sqlite3.connect(service.store.database_path)) as connection:
        connection.execute("UPDATE workflow SET current_stage = 'integration' WHERE id = 1")
        connection.commit()

    recovered = WorkflowService(tmp_path)
    assert recovered.status()["current_stage"] == "integration"
    resumed = recovered.resume()
    assert resumed["status"] == "active"
    assert resumed["current_stage"] == "project_discovery"
    assert recovered.stop()["status"] == "stopped"
    assert WorkflowService(tmp_path).resume()["status"] == "active"


def test_mandatory_approval_gate_blocks_until_approved(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    service = WorkflowService(tmp_path)
    service.start()
    for _ in range(5):
        state = service.continue_workflow()
    assert state["current_stage"] == "requirements_review"

    with pytest.raises(StateError, match="requires approval"):
        service.continue_workflow()

    service.store.set_approval("requirements_review", "approved")
    assert service.continue_workflow()["current_stage"] == "system_architecture"


def test_invalid_lifecycle_transitions_are_actionable(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    service = WorkflowService(tmp_path)

    with pytest.raises(StateError, match="active workflow"):
        service.pause()
    with pytest.raises(StateError, match="must be active"):
        service.continue_workflow()
    with pytest.raises(StateError, match="active or paused"):
        service.stop()
    with pytest.raises(StateError, match="paused or stopped"):
        service.resume()
    with pytest.raises(StateError, match="unknown workflow stage"):
        service.approve("not_a_stage")
    with pytest.raises(StateError, match="cannot be blank"):
        service.revise("requirements_review", " ")
