"""Transactional SQLite state store with snapshots and checkpoints."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentic_framework.exceptions import StateError

_SCHEMA = """
CREATE TABLE IF NOT EXISTS project (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    root TEXT NOT NULL,
    initialized_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workflow (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    status TEXT NOT NULL,
    current_stage TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    dependencies_json TEXT NOT NULL DEFAULT '[]',
    expected_outputs_json TEXT NOT NULL DEFAULT '[]',
    acceptance_criteria_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS approvals (
    stage_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    feedback TEXT,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reason TEXT NOT NULL,
    state_json TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
PRAGMA user_version = 1;
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


class RuntimeStore:
    """Own the runtime database, inspection snapshots, and JSONL event history."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.expanduser().resolve()
        self.runtime = self.project_root / ".agentic"
        self.database_path = self.runtime / "database" / "agentic.db"
        self.state_dir = self.runtime / "state"
        self.events_path = self.runtime / "logs" / "events.jsonl"

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = _now()
        with self.connect() as connection:
            connection.executescript(_SCHEMA)
            connection.execute(
                "INSERT OR IGNORE INTO project(id, root, initialized_at) VALUES(1, ?, ?)",
                (str(self.project_root), timestamp),
            )
            connection.execute(
                "INSERT OR IGNORE INTO workflow(id, status, current_stage, updated_at) "
                "VALUES(1, 'not_started', 'project_initialization', ?)",
                (timestamp,),
            )
        self.write_snapshots()
        self.events_path.touch(exist_ok=True)

    def workflow(self) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT status, current_stage, updated_at FROM workflow WHERE id = 1"
            ).fetchone()
        if row is None:
            raise StateError("runtime workflow state is missing; run adt init")
        return dict(row)

    def tasks(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT task_id, agent_id, title, status FROM tasks ORDER BY task_id"
            ).fetchall()
        return [dict(row) for row in rows]

    def approvals(self, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT stage_id, status, feedback, updated_at FROM approvals"
        parameters: tuple[str, ...] = ()
        if status:
            query += " WHERE status = ?"
            parameters = (status,)
        query += " ORDER BY stage_id"
        with self.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def approval_status(self, stage_id: str) -> str | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT status FROM approvals WHERE stage_id = ?", (stage_id,)
            ).fetchone()
        return row["status"] if row else None

    def set_approval(self, stage_id: str, status: str, feedback: str | None = None) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO approvals(stage_id, status, feedback, updated_at) VALUES(?, ?, ?, ?) "
                "ON CONFLICT(stage_id) DO UPDATE SET status=excluded.status, "
                "feedback=excluded.feedback, updated_at=excluded.updated_at",
                (stage_id, status, feedback, _now()),
            )
        self.record_event("approval_updated", {"stage_id": stage_id, "status": status})
        self.write_snapshots()

    def update_workflow(self, status: str, current_stage: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE workflow SET status = ?, current_stage = ?, updated_at = ? WHERE id = 1",
                (status, current_stage, _now()),
            )
        self.record_event("workflow_updated", {"status": status, "stage": current_stage})
        self.write_snapshots()

    def record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        timestamp = _now()
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO events(event_type, payload_json, created_at) VALUES(?, ?, ?)",
                (event_type, serialized, timestamp),
            )
        entry = json.dumps(
            {"timestamp": timestamp, "type": event_type, "payload": payload},
            sort_keys=True,
            separators=(",", ":"),
        )
        with self.events_path.open("a", encoding="utf-8") as event_log:
            event_log.write(entry + "\n")

    def create_checkpoint(self, reason: str) -> int:
        state = {"workflow": self.workflow(), "tasks": self.tasks()}
        serialized = json.dumps(state, sort_keys=True, separators=(",", ":"))
        checksum = hashlib.sha256(serialized.encode()).hexdigest()
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO checkpoints(reason, state_json, sha256, created_at) "
                "VALUES(?, ?, ?, ?)",
                (reason, serialized, checksum, _now()),
            )
            checkpoint_id = int(cursor.lastrowid)
        self.record_event("checkpoint_created", {"id": checkpoint_id, "reason": reason})
        return checkpoint_id

    def validate_latest_checkpoint(self) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT state_json, sha256 FROM checkpoints ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        checksum = hashlib.sha256(row["state_json"].encode()).hexdigest()
        if checksum != row["sha256"]:
            raise StateError("latest checkpoint failed integrity validation")
        try:
            value = json.loads(row["state_json"])
        except json.JSONDecodeError as exc:
            raise StateError("latest checkpoint contains invalid state") from exc
        workflow = value.get("workflow") if isinstance(value, dict) else None
        if (
            not isinstance(workflow, dict)
            or not isinstance(workflow.get("status"), str)
            or not isinstance(workflow.get("current_stage"), str)
        ):
            raise StateError("latest checkpoint has an invalid structure")
        return value

    @staticmethod
    def _atomic_json(path: Path, value: object) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)

    def write_snapshots(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        workflow = self.workflow()
        tasks = self.tasks()
        self._atomic_json(self.state_dir / "workflow.json", workflow)
        self._atomic_json(self.state_dir / "tasks.json", tasks)
        self._atomic_json(
            self.state_dir / "execution.json",
            {"status": workflow["status"], "updated_at": workflow["updated_at"]},
        )
