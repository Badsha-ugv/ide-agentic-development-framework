import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from agentic_framework.core.initialization import initialize_project
from agentic_framework.exceptions import StateError
from agentic_framework.state import RuntimeStore


def test_initialization_creates_database_snapshots_and_event_log(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    store = RuntimeStore(tmp_path)

    assert store.database_path.is_file()
    assert store.events_path.is_file()
    assert store.workflow()["status"] == "not_started"
    assert json.loads((store.state_dir / "workflow.json").read_text())["current_stage"] == (
        "project_discovery"
    )
    assert json.loads((store.state_dir / "tasks.json").read_text()) == []
    with closing(sqlite3.connect(store.database_path)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {
        "project",
        "workflow",
        "tasks",
        "approvals",
        "checkpoints",
        "events",
        "stage_executions",
        "artifacts",
        "revisions",
    } <= tables
    assert store.execution("project_initialization")["status"] == "completed"
    assert store.artifacts("project_initialization")[0]["path"] == (
        ".agentic/reports/initialization.md"
    )


def test_database_reinitialization_preserves_workflow_state(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    store = RuntimeStore(tmp_path)
    store.update_workflow("active", "project_discovery")

    initialize_project(tmp_path, initialize_git=False)

    assert RuntimeStore(tmp_path).workflow()["current_stage"] == "project_discovery"


def test_checkpoint_integrity_failure_is_reported(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    store = RuntimeStore(tmp_path)
    store.update_workflow("paused", "project_discovery")
    checkpoint_id = store.create_checkpoint("test")
    with closing(sqlite3.connect(store.database_path)) as connection:
        connection.execute(
            "UPDATE checkpoints SET state_json = ? WHERE id = ?",
            ('{"workflow":"tampered"}', checkpoint_id),
        )
        connection.commit()

    with pytest.raises(StateError, match="integrity validation"):
        store.validate_latest_checkpoint()
