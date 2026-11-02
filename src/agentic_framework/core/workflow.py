"""Persistent workflow lifecycle and recovery behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentic_framework.adapters.generator import APPROVAL_STAGES, STAGES
from agentic_framework.exceptions import StateError
from agentic_framework.state import RuntimeStore


@dataclass(slots=True)
class WorkflowService:
    """Apply validated lifecycle transitions to a project runtime."""

    project_root: Path
    store: RuntimeStore = field(init=False)

    def __post_init__(self) -> None:
        self.store = RuntimeStore(self.project_root)
        if not self.store.database_path.is_file():
            raise StateError(
                f"runtime database does not exist; run adt init: {self.store.database_path}"
            )

    def status(self) -> dict[str, Any]:
        return self.store.workflow()

    def start(self) -> dict[str, Any]:
        current = self.status()
        if current["status"] == "paused":
            raise StateError("workflow is paused; use adt resume")
        if current["status"] != "active":
            self.store.update_workflow("active", current["current_stage"])
        return self.status()

    def pause(self) -> dict[str, Any]:
        current = self.status()
        if current["status"] != "active":
            raise StateError("only an active workflow can be paused")
        self.store.update_workflow("paused", current["current_stage"])
        self.store.create_checkpoint("pause")
        return self.status()

    def stop(self) -> dict[str, Any]:
        current = self.status()
        if current["status"] not in {"active", "paused"}:
            raise StateError("only an active or paused workflow can be stopped")
        self.store.update_workflow("stopped", current["current_stage"])
        self.store.create_checkpoint("stop")
        return self.status()

    def resume(self) -> dict[str, Any]:
        current = self.status()
        if current["status"] not in {"paused", "stopped"}:
            raise StateError("only a paused or stopped workflow can be resumed")
        checkpoint = self.store.validate_latest_checkpoint()
        if checkpoint is None:
            raise StateError("cannot resume without a valid checkpoint")
        checkpoint_stage = checkpoint["workflow"]["current_stage"]
        if checkpoint_stage not in STAGES:
            raise StateError(f"checkpoint contains an unknown workflow stage: {checkpoint_stage}")
        self.store.update_workflow("active", checkpoint_stage)
        return self.status()

    def continue_workflow(self) -> dict[str, Any]:
        current = self.status()
        if current["status"] != "active":
            raise StateError("workflow must be active before it can continue")
        stage = current["current_stage"]
        if stage not in STAGES:
            raise StateError(f"runtime contains an unknown workflow stage: {stage}")
        if stage in APPROVAL_STAGES and self.store.approval_status(stage) != "approved":
            raise StateError(f"stage requires approval before continuing: {stage}")
        index = STAGES.index(stage)
        next_stage = STAGES[min(index + 1, len(STAGES) - 1)]
        next_status = "completed" if next_stage == "completed" else "active"
        self.store.update_workflow(next_status, next_stage)
        self.store.create_checkpoint("stage_transition")
        return self.status()

    def approve(self, stage: str) -> None:
        if stage not in STAGES:
            raise StateError(f"unknown workflow stage: {stage}")
        self.store.set_approval(stage, "approved")

    def revise(self, stage: str, feedback: str) -> None:
        if stage not in STAGES:
            raise StateError(f"unknown workflow stage: {stage}")
        if not feedback.strip():
            raise StateError("revision feedback cannot be blank")
        self.store.set_approval(stage, "revision_requested", feedback.strip())
