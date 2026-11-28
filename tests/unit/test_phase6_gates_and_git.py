import json
import subprocess
from pathlib import Path

import pytest

from agentic_framework.core.gates import BugReport, BugSeverity, validate_security_findings_gate
from agentic_framework.core.initialization import initialize_project
from agentic_framework.core.workflow import WorkflowService
from agentic_framework.exceptions import StateError
from agentic_framework.integrations.git import create_task_branch, inspect_git_state, safe_commit


def test_git_wrapper_inspects_branches_and_blocks_secrets(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    sha = safe_commit(tmp_path, "Initial commit", ["README.md"])
    assert sha

    state = inspect_git_state(tmp_path)
    assert state.is_repo is True
    assert state.dirty is False

    branch = create_task_branch(tmp_path, "feat/phase6-test")
    assert branch == "feat/phase6-test"

    (tmp_path / ".env").write_text("SECRET=123\n", encoding="utf-8")
    with pytest.raises(StateError, match="potential secret"):
        safe_commit(tmp_path, "Bad commit", [".env"])


def test_security_findings_gate_blocks_open_high_severity(tmp_path: Path) -> None:
    reports = tmp_path / "docs" / "reports"
    reports.mkdir(parents=True)
    findings_file = reports / "security-findings.json"
    findings_file.write_text(
        json.dumps(
            {
                "findings": [
                    {"title": "SQL injection in search", "severity": "high", "status": "open"}
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(StateError, match="SQL injection in search"):
        validate_security_findings_gate(tmp_path)

    findings_file.write_text(
        json.dumps(
            {
                "findings": [
                    {"title": "SQL injection in search", "severity": "high", "status": "resolved"}
                ]
            }
        ),
        encoding="utf-8",
    )
    validate_security_findings_gate(tmp_path)


def test_bug_report_validation_and_minimal_approval_policy(tmp_path: Path) -> None:
    bug = BugReport(
        title="Login returns 500 on empty password",
        description="Submitting blank password crashes handler",
        steps_to_reproduce=["POST /login with empty password"],
        expected_result="400 validation error",
        actual_result="500 Internal Server Error",
        severity=BugSeverity.HIGH,
        affected_module="auth/views.py",
        suggested_resolution="Validate non-empty password in serializer",
    )
    assert bug.severity is BugSeverity.HIGH

    initialize_project(tmp_path, initialize_git=False)
    cfg = tmp_path / ".agentic" / "config.yaml"
    cfg.write_text(
        cfg.read_text(encoding="utf-8").replace(
            "approval_policy: strict",
            "approval_policy: minimal",
        ),
        encoding="utf-8",
    )
    service = WorkflowService(tmp_path)
    service.start()
    service.store.update_workflow("active", "requirements_review")
    service.continue_workflow()
    for rel in service.stage_contract().expected_outputs:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Doc\n\nContent.\n", encoding="utf-8")
        service.register_artifact(rel)

    res = service.complete_stage()
    assert res["current_stage"] == "system_architecture"
