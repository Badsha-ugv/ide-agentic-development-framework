"""Persistent workflow execution, validation, approval, and recovery behavior."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentic_framework.core.stages import (
    APPROVAL_STAGES,
    CONTRACT_BY_ID,
    STAGES,
    StageContract,
)
from agentic_framework.exceptions import RequirementsError, StateError
from agentic_framework.requirements_manager import ScreenshotManager
from agentic_framework.state import RuntimeStore


@dataclass(slots=True)
class WorkflowService:
    """Apply validated lifecycle transitions to a project runtime."""

    project_root: Path
    store: RuntimeStore = field(init=False)

    def __post_init__(self) -> None:
        self.project_root = self.project_root.expanduser().resolve()
        self.store = RuntimeStore(self.project_root)
        if not self.store.database_path.is_file():
            raise StateError(
                f"runtime database does not exist; run adt init: {self.store.database_path}"
            )
        # Additive and idempotent: upgrades v1 runtimes before v2 tables are read.
        self.store.initialize()

    def status(self) -> dict[str, Any]:
        """Return workflow state together with the current execution gate."""

        workflow = self.store.workflow()
        stage = workflow["current_stage"]
        if stage not in CONTRACT_BY_ID:
            raise StateError(f"runtime contains an unknown workflow stage: {stage}")
        return {
            **workflow,
            "execution": self.store.execution(stage),
            "approval": self.store.approval_status(stage),
            "artifacts": self.store.artifacts(stage),
        }

    def stage_contract(self, stage: str | None = None) -> StageContract:
        """Return the requested contract, defaulting to the current stage."""

        stage_id = stage or self.store.workflow()["current_stage"]
        try:
            return CONTRACT_BY_ID[stage_id]
        except KeyError as exc:
            raise StateError(f"unknown workflow stage: {stage_id}") from exc

    def start(self) -> dict[str, Any]:
        current = self.status()
        if current["status"] == "paused":
            raise StateError("workflow is paused; use adt resume")
        if current["status"] == "completed":
            raise StateError("workflow is already completed")
        if current["status"] != "active":
            self.store.update_workflow("active", current["current_stage"])
        return self.continue_workflow()

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
        """Prepare or resume the current stage without advancing it."""

        current = self.status()
        if current["status"] != "active":
            raise StateError("workflow must be active before it can continue; run adt start")
        stage = current["current_stage"]
        execution = current["execution"]
        if execution["status"] == "awaiting_approval":
            raise StateError(
                f"stage is awaiting review; use adt approve {stage} or adt revise {stage} FEEDBACK"
            )
        if execution["status"] == "completed":
            raise StateError(f"stage is already complete: {stage}")
        contract = self.stage_contract(stage)
        if stage in {"ui_ux_design", "design_review"}:
            try:
                ScreenshotManager(self.project_root).sync()
            except RequirementsError as exc:
                raise StateError(f"cannot prepare visual references: {exc}") from exc
        if execution["status"] == "failed" and execution["attempt_count"] >= contract.max_attempts:
            self.store.update_execution(
                stage,
                "blocked",
                blocker=f"maximum attempts reached ({contract.max_attempts})",
            )
            raise StateError(
                f"stage reached its retry limit ({contract.max_attempts}); "
                "resolve the blocker first"
            )
        if execution["status"] != "in_progress":
            self.store.update_execution(
                stage,
                "in_progress",
                current_task=contract.objective,
                increment_attempt=True,
            )
        return self.execution_plan()

    def execution_plan(self) -> dict[str, Any]:
        """Return the IDE-agent contract for the current stage."""

        current = self.status()
        contract = self.stage_contract(current["current_stage"])
        return {
            **current,
            "contract": contract.as_dict(),
            "contract_file": ".agentic/execution-contracts.yaml",
        }

    def register_artifact(self, path: str, stage: str | None = None) -> dict[str, Any]:
        """Register a deliverable for the active stage with immutable metadata."""

        current = self.status()
        stage_id = stage or current["current_stage"]
        if stage_id != current["current_stage"]:
            raise StateError("artifacts can only be registered for the current workflow stage")
        if current["execution"]["status"] != "in_progress":
            raise StateError("current stage is not in progress; run adt continue first")
        self.stage_contract(stage_id)
        return self.store.register_artifact(stage_id, path)

    def set_current_task(self, description: str) -> dict[str, Any]:
        """Persist a stage-scoped IDE-agent task without changing workflow position."""

        if not description.strip():
            raise StateError("current task description cannot be blank")
        current = self.status()
        if current["status"] != "active" or current["execution"]["status"] != "in_progress":
            raise StateError("current stage must be active and in progress; run adt continue first")
        self.store.update_execution(
            current["current_stage"],
            "in_progress",
            current_task=description.strip(),
        )
        return self.status()

    def _required_output_files(self, contract: StageContract) -> list[Path]:
        files: list[Path] = []
        missing: list[str] = []
        for pattern in contract.expected_outputs:
            matches = sorted(path for path in self.project_root.glob(pattern) if path.is_file())
            if not matches:
                missing.append(pattern)
            else:
                files.extend(matches)
        if missing:
            raise StateError("required stage outputs are missing: " + ", ".join(missing))
        empty = [
            path.relative_to(self.project_root).as_posix()
            for path in files
            if path.stat().st_size == 0
        ]
        if empty:
            raise StateError("required stage outputs are empty: " + ", ".join(empty))
        return list(dict.fromkeys(files))

    def validate_current_stage(self) -> list[str]:
        """Validate output presence and registered hashes for the current stage."""

        current = self.status()
        stage = current["current_stage"]
        contract = self.stage_contract(stage)
        files = self._required_output_files(contract)
        registered = {item["path"]: item for item in self.store.artifacts(stage)}
        unregistered: list[str] = []
        stale: list[str] = []
        for path in files:
            relative = path.relative_to(self.project_root).as_posix()
            artifact = registered.get(relative)
            if artifact is None:
                unregistered.append(relative)
            elif artifact["sha256"] != self.store._file_sha256(path):
                stale.append(relative)
        if unregistered:
            raise StateError("required outputs are not registered: " + ", ".join(unregistered))
        if stale:
            raise StateError("registered outputs changed; register them again: " + ", ".join(stale))
        if stage in {"ui_ux_design", "design_review"}:
            self._validate_design_evidence()
        return [path.relative_to(self.project_root).as_posix() for path in files]

    def _read_evidence(self, relative: str) -> dict[str, Any]:
        path = self.project_root / relative
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StateError(f"invalid structured design evidence {relative}: {exc}") from exc
        if not isinstance(value, dict):
            raise StateError(f"structured design evidence must be an object: {relative}")
        return value

    def _validate_design_evidence(self) -> None:
        inputs = self._read_evidence("docs/ui-ux/design-inputs.json")
        methods = inputs.get("methods")
        supported = set(CONTRACT_BY_ID["ui_ux_design"].supported_design_inputs)
        if (
            not isinstance(methods, list)
            or not methods
            or any(not isinstance(method, str) or method not in supported for method in methods)
        ):
            raise StateError(
                "design-input evidence must select one or more supported methods: "
                + ", ".join(sorted(supported))
            )
        if "figma_mcp" in methods:
            figma = inputs.get("figma")
            if not isinstance(figma, dict) or figma.get("status") != "inspected":
                raise StateError(
                    "Figma is selected but authenticated MCP inspection is not recorded; "
                    "record the blocker instead of claiming completion"
                )
        if "screenshots" in methods:
            manifest = self._read_evidence("requirements/screenshots/manifest.json")
            screenshots = manifest.get("screenshots")
            if not isinstance(screenshots, list) or not screenshots:
                raise StateError(
                    "screenshot design input is selected but the screenshot manifest is empty"
                )

        evidence = self._read_evidence("docs/ui-ux/browser-verification.json")
        pages = evidence.get("pages")
        if evidence.get("passed") is not True or not isinstance(pages, list) or not pages:
            raise StateError("browser verification must pass and include every prototype page")
        required_viewports = {"desktop", "tablet", "mobile"}
        for page in pages:
            if not isinstance(page, dict) or not isinstance(page.get("id"), str):
                raise StateError("each browser-verified page must have a stable id")
            viewports = page.get("viewports")
            if (
                not isinstance(viewports, list)
                or any(not isinstance(viewport, str) for viewport in viewports)
                or not required_viewports <= set(viewports)
            ):
                raise StateError(
                    f"browser verification for {page['id']} must cover desktop, tablet, and mobile"
                )
            if page.get("interactions_passed") is not True:
                raise StateError(f"interactive controls did not pass for page: {page['id']}")
            screenshots = page.get("screenshots")
            if not isinstance(screenshots, list) or not screenshots:
                raise StateError(f"rendered screenshots are missing for page: {page['id']}")
            for screenshot in screenshots:
                if not isinstance(screenshot, str):
                    raise StateError(f"invalid rendered screenshot path for page: {page['id']}")
                relative = Path(screenshot)
                rendered = (self.project_root / relative).resolve()
                allowed = (
                    self.project_root / "design-prototype/verification-screenshots"
                ).resolve()
                if (
                    relative.is_absolute()
                    or ".." in relative.parts
                    or not rendered.is_relative_to(allowed)
                    or not rendered.is_file()
                    or rendered.is_symlink()
                ):
                    raise StateError(
                        f"browser evidence references an unsafe or missing screenshot: {screenshot}"
                    )

    def complete_stage(self) -> dict[str, Any]:
        """Validate and complete the current stage, stopping at approval gates."""

        current = self.status()
        stage = current["current_stage"]
        if current["status"] != "active" or current["execution"]["status"] != "in_progress":
            raise StateError("current stage must be active and in progress before completion")
        self.validate_current_stage()
        if stage in APPROVAL_STAGES:
            self.store.set_approval(stage, "pending")
            self.store.update_execution(stage, "awaiting_approval")
            self.store.create_checkpoint("approval_requested")
            return self.status()
        self.store.update_execution(stage, "completed")
        self.store.create_checkpoint("stage_completed")
        self._advance(stage)
        return self.status()

    def fail_stage(self, message: str, *, blocked: bool = False) -> dict[str, Any]:
        """Record a recoverable failure or explicit blocker without advancing."""

        if not message.strip():
            raise StateError("failure or blocker message cannot be blank")
        current = self.status()
        if current["status"] != "active":
            raise StateError("only an active workflow stage can fail or block")
        state = "blocked" if blocked else "failed"
        self.store.update_execution(
            current["current_stage"],
            state,
            blocker=message.strip() if blocked else None,
            error=None if blocked else message.strip(),
        )
        self.store.create_checkpoint(f"stage_{state}")
        return self.status()

    def _advance(self, completed_stage: str) -> None:
        index = STAGES.index(completed_stage)
        next_stage = STAGES[min(index + 1, len(STAGES) - 1)]
        next_status = "completed" if next_stage == "completed" else "active"
        self.store.update_workflow(next_status, next_stage)
        if next_stage == "completed":
            self.store.update_execution("completed", "completed")
        self.store.create_checkpoint("stage_transition")

    def approve(self, stage: str) -> dict[str, Any]:
        if stage not in CONTRACT_BY_ID:
            raise StateError(f"unknown workflow stage: {stage}")
        if stage not in APPROVAL_STAGES:
            raise StateError(f"stage is not an approval gate: {stage}")
        current = self.status()
        if current["current_stage"] != stage:
            raise StateError(f"only the current stage can be approved: {current['current_stage']}")
        if current["execution"]["status"] != "awaiting_approval":
            raise StateError(f"stage is not awaiting approval: {stage}")
        self.validate_current_stage()
        self.store.set_approval(stage, "approved")
        self.store.update_execution(stage, "completed")
        self.store.create_checkpoint("stage_approved")
        self._advance(stage)
        return self.status()

    def revise(self, stage: str, feedback: str) -> dict[str, Any]:
        if stage not in CONTRACT_BY_ID:
            raise StateError(f"unknown workflow stage: {stage}")
        if stage not in APPROVAL_STAGES:
            raise StateError(f"stage is not an approval gate: {stage}")
        if not feedback.strip():
            raise StateError("revision feedback cannot be blank")
        current = self.status()
        if current["current_stage"] != stage:
            raise StateError(f"only the current stage can be revised: {current['current_stage']}")
        if current["execution"]["status"] != "awaiting_approval":
            raise StateError(f"stage is not awaiting approval: {stage}")
        # Preserve exactly the bytes that were validated and submitted for review.
        self.validate_current_stage()

        revision_number = len(self.store.revisions(stage)) + 1
        relative_snapshot = Path(".agentic") / "revisions" / stage / f"revision-{revision_number}"
        snapshot = self.project_root / relative_snapshot
        for artifact in self.store.artifacts(stage):
            source = self.project_root / artifact["path"]
            destination = snapshot / artifact["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        self.store.record_revision(stage, feedback.strip(), relative_snapshot.as_posix())
        self.store.set_approval(stage, "revision_requested", feedback.strip())
        self.store.update_execution(stage, "in_progress", increment_attempt=True)
        self.store.create_checkpoint("revision_requested")
        return self.status()
