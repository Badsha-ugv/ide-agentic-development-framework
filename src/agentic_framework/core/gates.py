"""Evidence-based QA, security, and bug-reporting quality gates."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from pydantic import Field

from agentic_framework.core.config import StrictModel
from agentic_framework.exceptions import StateError


class BugSeverity(StrEnum):
    """Standardized defect severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BugReport(StrictModel):
    """Structured SQA defect report required by Section 9."""

    title: str = Field(min_length=3)
    description: str = Field(min_length=3)
    steps_to_reproduce: list[str] = Field(min_length=1)
    expected_result: str = Field(min_length=1)
    actual_result: str = Field(min_length=1)
    severity: BugSeverity
    affected_module: str = Field(min_length=1)
    suggested_resolution: str = Field(min_length=1)


def validate_security_findings_gate(project_root: Path) -> None:
    """Block security_testing completion if unresolved critical/high findings exist."""

    findings_path = project_root.expanduser().resolve() / "docs/reports/security-findings.json"
    if not findings_path.is_file():
        return
    try:
        payload = json.loads(findings_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateError(f"invalid security findings report: {exc}") from exc
    findings = payload.get("findings") if isinstance(payload, dict) else None
    if not isinstance(findings, list):
        raise StateError("security-findings.json must contain a 'findings' list")
    blocking = [
        str(item.get("title", "unnamed finding"))
        for item in findings
        if isinstance(item, dict)
        and str(item.get("severity", "")).lower() in {"critical", "high"}
        and str(item.get("status", "open")).lower() not in {"resolved", "fixed", "mitigated"}
    ]
    if blocking:
        raise StateError(
            "unresolved critical/high security findings block completion: "
            + ", ".join(blocking)
        )
