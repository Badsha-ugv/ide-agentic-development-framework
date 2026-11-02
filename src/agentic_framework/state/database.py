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
CREATE TABLE IF NOT EXISTS stage_executions (
    stage_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    current_task TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    blocker TEXT,
    error TEXT,
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_id TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size INTEGER NOT NULL,
    revision INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(stage_id, path, revision)
);
CREATE TABLE IF NOT EXISTS revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_id TEXT NOT NULL,
    feedback TEXT NOT NULL,
    snapshot_dir TEXT NOT NULL,
    created_at TEXT NOT NULL
);
PRAGMA user_version = 2;
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
            execution_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(stage_executions)")
            }
            if "current_task" not in execution_columns:
                connection.execute("ALTER TABLE stage_executions ADD COLUMN current_task TEXT")
            connection.execute(
                "INSERT OR IGNORE INTO project(id, root, initialized_at) VALUES(1, ?, ?)",
                (str(self.project_root), timestamp),
            )
            connection.execute(
                "INSERT OR IGNORE INTO workflow(id, status, current_stage, updated_at) "
                "VALUES(1, 'not_started', 'project_initialization', ?)",
                (timestamp,),
            )
            connection.execute("PRAGMA user_version = 2")
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

    def execution(self, stage_id: str) -> dict[str, Any]:
        """Return execution state, creating a pending row during safe migration."""

        with self.connect() as connection:
            row = connection.execute(
                "SELECT stage_id, status, current_task, attempt_count, blocker, error, started_at, "
                "completed_at, updated_at FROM stage_executions WHERE stage_id = ?",
                (stage_id,),
            ).fetchone()
            if row is None:
                timestamp = _now()
                connection.execute(
                    "INSERT INTO stage_executions(stage_id, status, updated_at) "
                    "VALUES(?, 'pending', ?)",
                    (stage_id, timestamp),
                )
                row = connection.execute(
                    "SELECT stage_id, status, current_task, attempt_count, blocker, error, "
                    "started_at, "
                    "completed_at, updated_at FROM stage_executions WHERE stage_id = ?",
                    (stage_id,),
                ).fetchone()
        if row is None:  # pragma: no cover - protected by the insert above
            raise StateError(f"cannot create execution state for stage: {stage_id}")
        return dict(row)

    def executions(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT stage_id, status, current_task, attempt_count, blocker, error, started_at, "
                "completed_at, updated_at FROM stage_executions ORDER BY rowid"
            ).fetchall()
        return [dict(row) for row in rows]

    def update_execution(
        self,
        stage_id: str,
        status: str,
        *,
        current_task: str | None = None,
        blocker: str | None = None,
        error: str | None = None,
        increment_attempt: bool = False,
    ) -> dict[str, Any]:
        """Persist one execution transition without changing the workflow stage."""

        current = self.execution(stage_id)
        timestamp = _now()
        attempts = current["attempt_count"] + (1 if increment_attempt else 0)
        current_task = current_task if current_task is not None else current["current_task"]
        started_at = current["started_at"]
        if status == "in_progress" and started_at is None:
            started_at = timestamp
        completed_at = timestamp if status == "completed" else current["completed_at"]
        if status not in {"blocked", "failed"}:
            blocker = None
            error = None
        with self.connect() as connection:
            connection.execute(
                "UPDATE stage_executions SET status = ?, current_task = ?, attempt_count = ?, "
                "blocker = ?, "
                "error = ?, started_at = ?, completed_at = ?, updated_at = ? "
                "WHERE stage_id = ?",
                (
                    status,
                    current_task,
                    attempts,
                    blocker,
                    error,
                    started_at,
                    completed_at,
                    timestamp,
                    stage_id,
                ),
            )
        self.record_event(
            "stage_execution_updated",
            {"stage_id": stage_id, "status": status, "attempt_count": attempts},
        )
        self.write_snapshots()
        return self.execution(stage_id)

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def register_artifact(self, stage_id: str, relative_path: str) -> dict[str, Any]:
        """Register a project artifact as a new immutable metadata revision."""

        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise StateError("artifact path must be project-relative without parent traversal")
        path = (self.project_root / relative).resolve()
        if not path.is_relative_to(self.project_root) or not path.is_file() or path.is_symlink():
            raise StateError(f"artifact must be a regular project file: {relative_path}")
        digest = self._file_sha256(path)
        with self.connect() as connection:
            previous = connection.execute(
                "SELECT revision, sha256 FROM artifacts WHERE stage_id = ? AND path = ? "
                "ORDER BY revision DESC LIMIT 1",
                (stage_id, relative.as_posix()),
            ).fetchone()
            if previous and previous["sha256"] == digest:
                revision = previous["revision"]
            else:
                revision = (previous["revision"] if previous else 0) + 1
                connection.execute(
                    "INSERT INTO artifacts(stage_id, path, sha256, size, revision, created_at) "
                    "VALUES(?, ?, ?, ?, ?, ?)",
                    (
                        stage_id,
                        relative.as_posix(),
                        digest,
                        path.stat().st_size,
                        revision,
                        _now(),
                    ),
                )
        self.record_event(
            "artifact_registered",
            {"stage_id": stage_id, "path": relative.as_posix(), "revision": revision},
        )
        self.write_snapshots()
        return {
            "stage_id": stage_id,
            "path": relative.as_posix(),
            "sha256": digest,
            "size": path.stat().st_size,
            "revision": revision,
        }

    def artifacts(self, stage_id: str | None = None) -> list[dict[str, Any]]:
        query = (
            "SELECT a.stage_id, a.path, a.sha256, a.size, a.revision, a.created_at "
            "FROM artifacts a JOIN (SELECT stage_id, path, MAX(revision) AS revision "
            "FROM artifacts GROUP BY stage_id, path) latest "
            "ON a.stage_id = latest.stage_id AND a.path = latest.path "
            "AND a.revision = latest.revision"
        )
        parameters: tuple[str, ...] = ()
        if stage_id:
            query += " WHERE a.stage_id = ?"
            parameters = (stage_id,)
        query += " ORDER BY a.stage_id, a.path"
        with self.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def record_revision(self, stage_id: str, feedback: str, snapshot_dir: str) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO revisions(stage_id, feedback, snapshot_dir, created_at) "
                "VALUES(?, ?, ?, ?)",
                (stage_id, feedback, snapshot_dir, _now()),
            )
            revision_id = int(cursor.lastrowid)
        self.record_event(
            "revision_recorded", {"id": revision_id, "stage_id": stage_id}
        )
        return revision_id

    def revisions(self, stage_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT id, stage_id, feedback, snapshot_dir, created_at FROM revisions"
        parameters: tuple[str, ...] = ()
        if stage_id:
            query += " WHERE stage_id = ?"
            parameters = (stage_id,)
        query += " ORDER BY id"
        with self.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
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
        state = {
            "workflow": self.workflow(),
            "tasks": self.tasks(),
            "executions": self.executions(),
            "artifacts": self.artifacts(),
            "approvals": self.approvals(),
        }
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
            {
                "workflow_status": workflow["status"],
                "current_stage": workflow["current_stage"],
                "stage_execution": self.execution(workflow["current_stage"]),
                "artifacts": self.artifacts(workflow["current_stage"]),
                "updated_at": workflow["updated_at"],
            },
        )
