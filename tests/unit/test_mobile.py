import json
from pathlib import Path

import pytest

from agentic_framework.core.mobile import validate_mobile_evidence
from agentic_framework.core.project import inspect_project
from agentic_framework.exceptions import StateError


def test_mobile_stack_and_domain_detection(tmp_path: Path) -> None:
    (tmp_path / "pubspec.yaml").write_text("name: demo_mobile\n", encoding="utf-8")
    (tmp_path / "android").mkdir()
    (tmp_path / "android" / "build.gradle.kts").write_text("// gradle\n", encoding="utf-8")
    (tmp_path / "ios").mkdir()
    (tmp_path / "ios" / "Podfile").write_text("platform :ios, '15.0'\n", encoding="utf-8")

    inspection = inspect_project(tmp_path)
    assert "Flutter" in inspection.technologies
    assert "Android" in inspection.technologies
    assert "iOS" in inspection.technologies
    assert inspection.domain_status.mobile is True
    assert "mobile" in inspection.domain_status.summary


def test_validate_mobile_evidence_enforces_android_and_ios(tmp_path: Path) -> None:
    mobile_docs = tmp_path / "docs" / "mobile"
    mobile_docs.mkdir(parents=True)
    (mobile_docs / "implementation-manifest.json").write_text(
        json.dumps({"framework": "expo", "platforms": ["android", "ios"]}),
        encoding="utf-8",
    )
    (mobile_docs / "device-verification.json").write_text(
        json.dumps(
            {
                "passed": True,
                "android_passed": True,
                "ios_passed": False,
                "permissions_verified": True,
                "offline_verified": True,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(StateError, match="ios_passed"):
        validate_mobile_evidence(tmp_path)

    (mobile_docs / "device-verification.json").write_text(
        json.dumps(
            {
                "passed": True,
                "android_passed": True,
                "ios_passed": True,
                "permissions_verified": True,
                "offline_verified": True,
            }
        ),
        encoding="utf-8",
    )
    validate_mobile_evidence(tmp_path)
