import hashlib
import json
from pathlib import Path

import pytest

from agentic_framework.core.initialization import initialize_project
from agentic_framework.exceptions import RequirementsError
from agentic_framework.requirements_manager import RequirementsManager


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_entire_requirements_versioning_process(tmp_path: Path) -> None:
    initialize_project(tmp_path, initialize_git=False)
    inbox = tmp_path / "requirements" / "inbox"
    features = inbox / "features.md"
    notes = inbox / "notes.txt"
    diagram = inbox / "flow.pdf"
    first_features = b"REQ-001: Sign in\nUsers can sign in.\n\nREQ-002: Export\nExport CSV.\n"
    features.write_bytes(first_features)
    notes.write_text("Stakeholder notes\n", encoding="utf-8")
    diagram.write_bytes(b"%PDF-original-bytes")
    manager = RequirementsManager(tmp_path)

    first = manager.ingest()

    assert first.version == "version-001"
    assert first.previous_version is None
    assert first.duplicate is False
    assert first.file_count == 3
    assert first.requirement_count == 2
    assert first.impact_report is None
    assert features.read_bytes() == first_features
    assert diagram.read_bytes() == b"%PDF-original-bytes"
    first_path = tmp_path / "requirements" / "versions" / "version-001"
    first_manifest_before = (first_path / "manifest.json").read_bytes()
    first_sources_before = {
        path.relative_to(first_path).as_posix(): path.read_bytes()
        for path in (first_path / "source-files").rglob("*")
        if path.is_file()
    }
    assert first_sources_before["source-files/features.md"] == first_features
    assert first_sources_before["source-files/flow.pdf"] == b"%PDF-original-bytes"
    manifest = _json(first_path / "manifest.json")
    files = {item["path"]: item for item in manifest["files"]}
    assert files["features.md"]["sha256"] == hashlib.sha256(first_features).hexdigest()
    assert files["flow.pdf"]["extraction"]["status"] == "unsupported"
    assert _json(first_path / "traceability.json")["requirements"][0]["id"] == "REQ-001"

    features.write_text(
        "REQ-001: Sign in\nUsers sign in with MFA.\n", encoding="utf-8"
    )
    notes.unlink()
    billing = inbox / "business" / "billing.md"
    billing.parent.mkdir()
    billing.write_text(
        "REQ-003: Billing\nAdministrators can create invoices.\n", encoding="utf-8"
    )

    second = manager.ingest()

    assert second.version == "version-002"
    assert second.previous_version == "version-001"
    assert second.comparison is not None
    assert second.comparison.files.added == ("business/billing.md",)
    assert second.comparison.files.modified == ("features.md",)
    assert second.comparison.files.removed == ("notes.txt",)
    assert second.comparison.files.unchanged == ("flow.pdf",)
    assert second.comparison.requirements.added == ("REQ-003",)
    assert second.comparison.requirements.modified == ("REQ-001",)
    assert second.comparison.requirements.removed == ("REQ-002",)
    assert second.impact_report is not None
    report = second.impact_report.read_text(encoding="utf-8")
    assert "version-001 to version-002" in report
    assert "`REQ-003`" in report
    assert "Architecture" in report
    assert (first_path / "manifest.json").read_bytes() == first_manifest_before
    assert {
        path.relative_to(first_path).as_posix(): path.read_bytes()
        for path in (first_path / "source-files").rglob("*")
        if path.is_file()
    } == first_sources_before
    assert features.read_text(encoding="utf-8").endswith("Users sign in with MFA.\n")

    duplicate = manager.ingest()

    assert duplicate.duplicate is True
    assert duplicate.version == "version-002"
    assert not (tmp_path / "requirements" / "versions" / "version-003").exists()


def test_reuses_legacy_empty_version_one_directory(tmp_path: Path) -> None:
    versions = tmp_path / "requirements" / "versions" / "version-001"
    versions.mkdir(parents=True)
    inbox = tmp_path / "requirements" / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "requirements.md").write_text("REQ-001: One\n", encoding="utf-8")

    result = RequirementsManager(tmp_path).ingest()

    assert result.version == "version-001"
    assert (versions / "manifest.json").is_file()


def test_rejects_empty_inbox_symlinks_and_incomplete_versions(tmp_path: Path) -> None:
    manager = RequirementsManager(tmp_path)
    with pytest.raises(RequirementsError, match="no requirement files"):
        manager.ingest()

    external = tmp_path / "external.md"
    external.write_text("REQ-001: External", encoding="utf-8")
    (manager.inbox / "linked.md").symlink_to(external)
    with pytest.raises(RequirementsError, match="symbolic links"):
        manager.ingest()
    (manager.inbox / "linked.md").unlink()

    (manager.inbox / "valid.md").write_text("REQ-001: Valid", encoding="utf-8")
    incomplete = manager.versions / "version-001"
    incomplete.mkdir()
    (incomplete / "partial").write_text("partial", encoding="utf-8")
    with pytest.raises(RequirementsError, match="incomplete requirements version"):
        manager.ingest()


def test_rejects_concurrent_ingestion_lock(tmp_path: Path) -> None:
    manager = RequirementsManager(tmp_path)
    manager.inbox.mkdir(parents=True)
    (manager.inbox / "valid.md").write_text("REQ-001: Valid", encoding="utf-8")
    lock = manager.requirements_root / ".ingestion.lock"
    lock.write_text("pid=unknown\n", encoding="utf-8")

    with pytest.raises(RequirementsError, match="already running"):
        manager.ingest()

    assert lock.is_file()


def test_detects_modification_of_published_source_copy(tmp_path: Path) -> None:
    manager = RequirementsManager(tmp_path)
    manager.inbox.mkdir(parents=True)
    (manager.inbox / "valid.md").write_text("REQ-001: Valid", encoding="utf-8")
    first = manager.ingest()
    copied = first.version_path / "source-files" / "valid.md"
    copied.write_text("REQ-001: Tampered", encoding="utf-8")

    with pytest.raises(RequirementsError, match="immutable source copy was modified"):
        manager.ingest()


def test_detects_modification_of_published_generated_artifact(tmp_path: Path) -> None:
    manager = RequirementsManager(tmp_path)
    manager.inbox.mkdir(parents=True)
    (manager.inbox / "valid.md").write_text("REQ-001: Valid", encoding="utf-8")
    first = manager.ingest()
    index = first.version_path / "requirements-index.json"
    index.write_text('{"requirements": []}\n', encoding="utf-8")

    with pytest.raises(RequirementsError, match="immutable version artifact was modified"):
        manager.ingest()
