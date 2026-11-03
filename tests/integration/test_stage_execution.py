import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from agentic_framework.core.initialization import initialize_project
from agentic_framework.core.stages import CONTRACTS
from agentic_framework.core.workflow import WorkflowService
from agentic_framework.exceptions import StateError


def _service(root: Path) -> WorkflowService:
    initialize_project(root, initialize_git=False)
    service = WorkflowService(root)
    service.start()
    return service


def _create_and_register_outputs(service: WorkflowService) -> list[Path]:
    outputs: list[Path] = []
    for relative in service.stage_contract().expected_outputs:
        assert "*" not in relative
        path = service.project_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n\nVerified stage deliverable.\n", encoding="utf-8")
        service.register_artifact(relative)
        outputs.append(path)
    return outputs


def test_initialization_completes_only_initialization_stage(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    service = WorkflowService(tmp_path)

    assert service.status()["current_stage"] == "project_discovery"
    assert service.status()["execution"]["status"] == "pending"
    assert service.store.execution("project_initialization")["status"] == "completed"


def test_continue_prepares_current_stage_without_advancing(tmp_path: Path) -> None:
    service = _service(tmp_path)
    first = service.status()
    second = service.continue_workflow()

    assert first["current_stage"] == second["current_stage"] == "project_discovery"
    assert second["execution"]["status"] == "in_progress"
    assert second["execution"]["attempt_count"] == 1


def test_completion_rejects_missing_discovery_outputs(tmp_path: Path) -> None:
    service = _service(tmp_path)

    with pytest.raises(StateError, match="required stage outputs are missing"):
        service.complete_stage()
    assert service.status()["current_stage"] == "project_discovery"


def test_discovery_outputs_must_be_registered_before_advancement(tmp_path: Path) -> None:
    service = _service(tmp_path)
    contract = service.stage_contract()
    for relative in contract.expected_outputs:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Discovery\n", encoding="utf-8")

    with pytest.raises(StateError, match="not registered"):
        service.complete_stage()
    for relative in contract.expected_outputs:
        service.register_artifact(relative)

    assert service.complete_stage()["current_stage"] == "requirements_ingestion"


def test_modified_artifact_hash_blocks_completion(tmp_path: Path) -> None:
    service = _service(tmp_path)
    outputs = _create_and_register_outputs(service)
    outputs[0].write_text("# Changed after registration\n", encoding="utf-8")

    with pytest.raises(StateError, match="registered outputs changed"):
        service.complete_stage()
    assert service.status()["current_stage"] == "project_discovery"


def test_artifact_changes_create_metadata_revisions(tmp_path: Path) -> None:
    service = _service(tmp_path)
    relative = service.stage_contract().expected_outputs[0]
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("first\n", encoding="utf-8")
    first = service.register_artifact(relative)
    path.write_text("second\n", encoding="utf-8")
    second = service.register_artifact(relative)

    assert first["revision"] == 1
    assert second["revision"] == 2
    assert first["sha256"] != second["sha256"]


def test_failure_and_retry_are_persisted_without_advancement(tmp_path: Path) -> None:
    service = _service(tmp_path)
    failed = service.fail_stage("generator command failed")

    assert failed["execution"]["status"] == "failed"
    assert failed["execution"]["error"] == "generator command failed"
    retried = WorkflowService(tmp_path).continue_workflow()
    assert retried["current_stage"] == "project_discovery"
    assert retried["execution"]["attempt_count"] == 2


def test_clarification_blocker_is_visible_after_reopen(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.fail_stage("Product owner must define retention policy", blocked=True)

    reopened = WorkflowService(tmp_path).status()
    assert reopened["execution"]["status"] == "blocked"
    assert reopened["execution"]["blocker"] == "Product owner must define retention policy"


def test_approval_revision_preserves_reviewed_snapshot(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.store.update_workflow("active", "requirements_review")
    service.continue_workflow()
    outputs = _create_and_register_outputs(service)
    waiting = service.complete_stage()

    assert waiting["execution"]["status"] == "awaiting_approval"
    revised = service.revise("requirements_review", "Clarify administrator permissions")
    assert revised["current_stage"] == "requirements_review"
    assert revised["execution"]["status"] == "in_progress"
    revision = service.store.revisions("requirements_review")[0]
    snapshot = tmp_path / revision["snapshot_dir"] / outputs[0].relative_to(tmp_path)
    assert snapshot.read_bytes() == outputs[0].read_bytes()

    service.complete_stage()
    approved = service.approve("requirements_review")
    assert approved["current_stage"] == "system_architecture"


def test_reviewed_artifact_cannot_change_before_approval(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.store.update_workflow("active", "requirements_review")
    service.continue_workflow()
    outputs = _create_and_register_outputs(service)
    service.complete_stage()
    outputs[0].write_text("# Unregistered review-time change\n", encoding="utf-8")

    with pytest.raises(StateError, match="registered outputs changed"):
        service.approve("requirements_review")
    assert service.status()["execution"]["status"] == "awaiting_approval"


def test_existing_v1_database_is_migrated_additively(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    database = tmp_path / ".agentic/database/agentic.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("DROP TABLE stage_executions")
        connection.execute("DROP TABLE artifacts")
        connection.execute("DROP TABLE revisions")
        connection.execute("PRAGMA user_version = 1")
        connection.commit()

    service = WorkflowService(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert version == 2
    assert {"stage_executions", "artifacts", "revisions"} <= tables
    assert service.status()["current_stage"] == "project_discovery"


def test_every_stage_has_a_complete_execution_contract() -> None:
    assert len(CONTRACTS) == 19
    for contract in CONTRACTS:
        assert contract.objective
        assert contract.agent
        assert contract.validation_criteria
        assert contract.completion_conditions
        assert contract.failure_behavior


def test_ui_ux_contract_is_final_visual_workflow_with_frontend_traceability() -> None:
    design = next(contract for contract in CONTRACTS if contract.id == "ui_ux_design")
    review = next(contract for contract in CONTRACTS if contract.id == "design_review")
    implementation = next(contract for contract in CONTRACTS if contract.id == "implementation")

    assert design.name == "UI/UX Design & Final Visual Prototype"
    assert design.supported_design_inputs == (
        "figma_mcp",
        "generated_prototype",
        "screenshots",
    )
    assert "docs/ui-ux/screenshot-reference-analysis.md" in design.expected_outputs
    assert "docs/ui-ux/browser-verification.json" in design.expected_outputs
    assert "design-prototype/versions/*/index.html" in design.expected_outputs
    assert review.approval_required is True
    assert "docs/reports/frontend-design-traceability.md" in implementation.expected_outputs


def test_design_evidence_requires_real_browser_and_figma_verification(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    service = WorkflowService(tmp_path)
    service.store.update_workflow("active", "ui_ux_design")
    service.continue_workflow()
    evidence_dir = tmp_path / "docs/ui-ux"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    screenshots = tmp_path / "design-prototype/verification-screenshots"
    screenshots.mkdir(parents=True)
    rendered = screenshots / "dashboard-desktop.png"
    rendered.write_bytes(b"rendered browser evidence")
    (evidence_dir / "design-inputs.json").write_text(
        json.dumps({"methods": ["generated_prototype"]}), encoding="utf-8"
    )
    verification = {
        "passed": True,
        "pages": [
            {
                "id": "dashboard",
                "viewports": ["desktop", "tablet", "mobile"],
                "interactions_passed": True,
                "screenshots": [
                    "design-prototype/verification-screenshots/dashboard-desktop.png"
                ],
            }
        ],
    }
    (evidence_dir / "browser-verification.json").write_text(
        json.dumps(verification), encoding="utf-8"
    )

    service._validate_design_evidence()

    (evidence_dir / "design-inputs.json").write_text("[]", encoding="utf-8")
    with pytest.raises(StateError, match="must be an object"):
        service._validate_design_evidence()
    (evidence_dir / "design-inputs.json").write_text(
        json.dumps({"methods": ["unsupported"]}), encoding="utf-8"
    )
    with pytest.raises(StateError, match="supported methods"):
        service._validate_design_evidence()
    (evidence_dir / "design-inputs.json").write_text(
        json.dumps({"methods": ["screenshots"]}), encoding="utf-8"
    )
    with pytest.raises(StateError, match="screenshot manifest is empty"):
        service._validate_design_evidence()
    (evidence_dir / "design-inputs.json").write_text(
        json.dumps({"methods": ["generated_prototype"]}), encoding="utf-8"
    )

    verification["passed"] = False
    (evidence_dir / "browser-verification.json").write_text(
        json.dumps(verification), encoding="utf-8"
    )
    with pytest.raises(StateError, match="browser verification must pass"):
        service._validate_design_evidence()
    verification["passed"] = True

    verification["pages"][0]["viewports"] = ["desktop"]
    (evidence_dir / "browser-verification.json").write_text(
        json.dumps(verification), encoding="utf-8"
    )
    with pytest.raises(StateError, match="desktop, tablet, and mobile"):
        service._validate_design_evidence()

    verification["pages"][0]["viewports"] = ["desktop", "tablet", "mobile"]
    verification["pages"][0]["interactions_passed"] = False
    (evidence_dir / "browser-verification.json").write_text(
        json.dumps(verification), encoding="utf-8"
    )
    with pytest.raises(StateError, match="interactive controls"):
        service._validate_design_evidence()

    verification["pages"][0]["interactions_passed"] = True
    verification["pages"][0]["screenshots"] = []
    (evidence_dir / "browser-verification.json").write_text(
        json.dumps(verification), encoding="utf-8"
    )
    with pytest.raises(StateError, match="rendered screenshots are missing"):
        service._validate_design_evidence()

    verification["pages"][0]["screenshots"] = ["outside.png"]
    (evidence_dir / "browser-verification.json").write_text(
        json.dumps(verification), encoding="utf-8"
    )
    with pytest.raises(StateError, match="unsafe or missing screenshot"):
        service._validate_design_evidence()

    (evidence_dir / "design-inputs.json").write_text(
        json.dumps({"methods": ["figma_mcp"], "figma": {"status": "unavailable"}}),
        encoding="utf-8",
    )
    with pytest.raises(StateError, match="authenticated MCP inspection"):
        service._validate_design_evidence()
